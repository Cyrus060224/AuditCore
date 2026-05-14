# -*- coding: utf-8 -*-
"""
RAG 检索引擎。
负责从 knowledge_base 目录读取 PDF 审计准则，构建本地 Chroma 向量库，
并按查询语义检索最相关的准则片段。
"""

from pathlib import Path
from typing import Iterable, List, Optional, Union

try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError as exc:
    raise ImportError(
        "Missing dependency: langchain-community. "
        "Please install project requirements before using AuditKnowledgeBase."
    ) from exc

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError as exc:
    raise ImportError(
        "Missing dependency: langchain-text-splitters. "
        "Please install project requirements before using AuditKnowledgeBase."
    ) from exc

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError as exc:
        raise ImportError(
            "Missing dependency: langchain-huggingface or langchain-community. "
            "Please install project requirements before using AuditKnowledgeBase."
        ) from exc

try:
    from langchain_chroma import Chroma
except ImportError:
    try:
        from langchain_community.vectorstores import Chroma
    except ImportError as exc:
        raise ImportError(
            "Missing dependency: langchain-chroma or langchain-community. "
            "Please install project requirements before using AuditKnowledgeBase."
        ) from exc

from core.utils import get_project_root


PathLike = Union[str, Path]


class AuditKnowledgeBase:
    """审计知识库，封装 PDF 入库和语义检索逻辑。"""

    def __init__(
        self,
        knowledge_base_dir: Optional[PathLike] = None,
        persist_dir: Optional[PathLike] = None,
        embedding_model: str = "shibing624/text2vec-base-chinese",
        chunk_size: int = 800,
        chunk_overlap: int = 120,
    ) -> None:
        """
        Args:
            knowledge_base_dir: PDF 知识库目录，默认使用项目根目录下的 knowledge_base。
            persist_dir: Chroma 持久化目录，默认使用项目根目录下的 chroma_db。
            embedding_model: HuggingFace 词向量模型名称。
            chunk_size: 文本切块长度。
            chunk_overlap: 相邻切块重叠长度。
        """
        project_root = get_project_root()
        self.knowledge_base_dir = self._resolve_path(
            knowledge_base_dir or project_root / "knowledge_base",
            base_dir=project_root,
        )
        self.persist_dir = self._resolve_path(
            persist_dir or project_root / "chroma_db",
            base_dir=project_root,
        )
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        try:
            self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load HuggingFace embedding model '{self.embedding_model}': {exc}"
            ) from exc

    def build_index(self, pdf_path: PathLike) -> int:
        """
        读取 knowledge_base 目录下的 PDF，切块并写入本地 Chroma 向量数据库。

        Args:
            pdf_path: PDF 文件、PDF 文件名或目录路径。相对路径会优先按
                knowledge_base 目录解析；传入目录时会递归读取其中所有 PDF。

        Returns:
            写入向量库的文本块数量。

        Raises:
            FileNotFoundError: 路径不存在或没有找到 PDF。
            ValueError: PDF 解析后没有可索引文本。
            RuntimeError: PDF 读取、切分或向量库写入失败。
        """
        pdf_files = self._collect_pdf_files(pdf_path)
        documents = []

        for pdf_file in pdf_files:
            try:
                loaded_docs = PyPDFLoader(str(pdf_file)).load()
            except Exception as exc:
                raise RuntimeError(f"Failed to load PDF '{pdf_file}': {exc}") from exc

            for doc in loaded_docs:
                doc.metadata["source"] = str(pdf_file)
            documents.extend(loaded_docs)

        if not documents:
            raise ValueError("No readable documents were loaded from the provided PDF path.")

        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", "。", "；", "，", " ", ""],
            )
            chunks = splitter.split_documents(documents)
        except Exception as exc:
            raise RuntimeError(f"Failed to split PDF documents: {exc}") from exc

        chunks = [chunk for chunk in chunks if chunk.page_content.strip()]
        if not chunks:
            raise ValueError("PDF documents did not contain indexable text.")

        try:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=str(self.persist_dir),
            )
            persist = getattr(vector_store, "persist", None)
            if callable(persist):
                persist()
        except Exception as exc:
            raise RuntimeError(f"Failed to persist Chroma index: {exc}") from exc

        return len(chunks)

    def retrieve_rules(self, query: str, top_k: int = 2) -> List[str]:
        """
        根据查询检索最相关的审计准则文本。

        Args:
            query: 查询字符串。
            top_k: 返回的准则片段数量。

        Returns:
            最相关的 k 条准则文本列表。无匹配结果时返回空列表。

        Raises:
            ValueError: 查询为空或 top_k 非正数。
            FileNotFoundError: Chroma 向量库尚未构建。
            RuntimeError: 检索过程失败。
        """
        query = (query or "").strip()
        if not query:
            raise ValueError("Query cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0.")
        if not self.persist_dir.exists():
            raise FileNotFoundError(
                f"Chroma index does not exist at '{self.persist_dir}'. "
                "Please call build_index() first."
            )

        try:
            vector_store = Chroma(
                persist_directory=str(self.persist_dir),
                embedding_function=self.embeddings,
            )
            results = vector_store.similarity_search(query, k=top_k)
        except Exception as exc:
            raise RuntimeError(f"Failed to retrieve rules from Chroma index: {exc}") from exc

        return [doc.page_content.strip() for doc in results if doc.page_content.strip()]

    def _collect_pdf_files(self, pdf_path: PathLike) -> List[Path]:
        """解析输入路径并收集 PDF 文件。"""
        resolved_path = self._resolve_pdf_input(pdf_path)
        if not resolved_path.exists():
            raise FileNotFoundError(f"PDF path does not exist: {resolved_path}")

        if resolved_path.is_file():
            if resolved_path.suffix.lower() != ".pdf":
                raise ValueError(f"Expected a PDF file, got: {resolved_path}")
            return [resolved_path]

        pdf_files = sorted(self._iter_pdf_files(resolved_path))
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in directory: {resolved_path}")

        return pdf_files

    def _resolve_pdf_input(self, pdf_path: PathLike) -> Path:
        """优先将相对 PDF 路径解析到 knowledge_base 目录下。"""
        path = Path(pdf_path).expanduser()
        if path.is_absolute():
            return path.resolve()

        knowledge_path = (self.knowledge_base_dir / path).resolve()
        if knowledge_path.exists():
            return knowledge_path

        return (get_project_root() / path).resolve()

    @staticmethod
    def _resolve_path(path: PathLike, base_dir: Path) -> Path:
        """跨平台解析路径，兼容绝对路径、相对路径和用户主目录。"""
        resolved = Path(path).expanduser()
        if not resolved.is_absolute():
            resolved = base_dir / resolved
        return resolved.resolve()

    @staticmethod
    def _iter_pdf_files(directory: Path) -> Iterable[Path]:
        """递归遍历目录中的 PDF 文件。"""
        return (
            path.resolve()
            for path in directory.rglob("*")
            if path.is_file() and path.suffix.lower() == ".pdf"
        )
