import pandas as pd
from datetime import datetime, timedelta

def generate_complex_audit_data():
    # 构造测试数据集
    data = [
        # --- 正常数据（用作干扰项） ---
        {"TransactionID": "TX-1001", "Date": "2026-05-01", "Department": "研发部", "Employee": "张三", "Category": "差旅费", "Amount": 1250.00, "Description": "北京出张机票"},
        {"TransactionID": "TX-1002", "Date": "2026-05-02", "Department": "市场部", "Employee": "李四", "Category": "办公用品", "Amount": 340.50, "Description": "采购打印纸和墨盒"},
        
        # --- 坑 1：负数金额（针对咱们刚刚写好的 RuleAgent） ---
        {"TransactionID": "TX-1003", "Date": "2026-05-03", "Department": "财务部", "Employee": "王五", "Category": "冲销", "Amount": -800.00, "Description": "上月账目错误红字冲销"},
        {"TransactionID": "TX-1004", "Date": "2026-05-05", "Department": "销售部", "Employee": "赵六", "Category": "退款", "Amount": -150.00, "Description": "客户定金退回"},
        
        # --- 坑 2：完全重复的行（针对 RuleAgent 的 duplicated 扫描） ---
        {"TransactionID": "TX-1005", "Date": "2026-05-08", "Department": "行政部", "Employee": "孙七", "Category": "餐饮招待", "Amount": 2000.00, "Description": "招待重要客户晚宴"},
        {"TransactionID": "TX-1005", "Date": "2026-05-08", "Department": "行政部", "Employee": "孙七", "Category": "餐饮招待", "Amount": 2000.00, "Description": "招待重要客户晚宴"}, # 完全重复，涉嫌重复报销
        
        # --- 坑 3：逻辑异常（留给以后的 FactCheckAgent 和大模型去抓） ---
        {"TransactionID": "TX-1007", "Date": "2026-05-10", "Department": "研发部", "Employee": "周八", "Category": "差旅费", "Amount": 49999.00, "Description": "采购高配GPU服务器"}, # 差旅费报销服务器？科目错报
        {"TransactionID": "TX-1008", "Date": "2026-05-16", "Department": "市场部", "Employee": "吴九", "Category": "团建费", "Amount": 8888.88, "Description": "周末KTV高档包厢消费"}, # 周末巨额娱乐消费
        
        # --- 坑 4：精准卡阈值（审计中常见的逃避审批手段） ---
        {"TransactionID": "TX-1009", "Date": "2026-05-18", "Department": "销售部", "Employee": "郑十", "Category": "公关费", "Amount": 4999.00, "Description": "礼品采购第一批"},
        {"TransactionID": "TX-1010", "Date": "2026-05-18", "Department": "销售部", "Employee": "郑十", "Category": "公关费", "Amount": 4999.00, "Description": "礼品采购第二批"}, # 故意拆分发票，规避5000元审批线
    ]

    # 转换为 DataFrame
    df = pd.DataFrame(data)
    
    # 保存为 Excel 文件
    file_name = "complex_audit_test.xlsx"
    df.to_excel(file_name, index=False)
    print(f"✅ 成功生成测试文件：{file_name}")
    print(f"总行数: {len(df)} 行。准备好让 AuditCore 进行挑战吧！")

if __name__ == "__main__":
    generate_complex_audit_data()