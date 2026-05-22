import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
import pandas as pd

# ==========================================
# 1. 企业级初始化：环境变量与合规日志系统
# ==========================================
load_dotenv()

log_filename = f"audit_sync_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据安全工具：员工姓名脱敏 (如：张三 -> 张*，欧阳锋 -> 欧**锋)
def mask_name(name: str) -> str:
    if not name: return ""
    if len(name) <= 2: return name[0] + "*"
    return name[0] + "*" * (len(name)-2) + name[-1]

# ==========================================
# 2. 核心业务类设计 (高可用与容错架构)
# ==========================================
class HCMIntegrationEngine:
    def __init__(self):
        self.api_url = os.getenv("HCM_API_BASE_URL", "https://api.hcm.com/v1")
        self.max_retries = int(os.getenv("MAX_RETRIES", 3))
        self.audit_records: List[Dict[str, Any]] = []

    def get_access_token(self) -> str:
        logger.info("🔐 正在请求 OAuth 2.0 授权 Token...")
        time.sleep(0.5)
        return "Bearer enterprise_token_final_v1"

    def fetch_attendance_data(self, token: str) -> List[Dict[str, Any]]:
        logger.info("📡 正在调用【时间管理 API】抓取跨系统考勤数据 (启用重试机制)...")
        
        # 模拟网络容错/重试机制
        for attempt in range(1, self.max_retries + 1):
            try:
                # 模拟网络抖动引发的超时
                if attempt == 1:
                    logger.warning(f"⚠️ 模拟网络抖动，第 {attempt} 次请求超时...")
                    time.sleep(1)
                    raise ConnectionError("API 网关响应超时")
                
                # 模拟第二次成功获取真实业务数据
                mock_data = [
                    {"emp_id": "EMP001", "name": "张三", "absent_days": 1, "overtime_hours": 12.5},
                    {"emp_id": "EMP002", "name": "李斯", "absent_days": 0, "overtime_hours": 5.0},
                    {"emp_id": "EMP003", "name": "王五", "absent_days": 3, "overtime_hours": 0},
                    {"emp_id": "EMP004", "name": "赵六", "absent_days": 0, "overtime_hours": 20.0} 
                ]
                logger.info(f"✅ 第 {attempt} 次请求成功！共拉取 {len(mock_data)} 条原始记录。")
                return mock_data
            
            except Exception as e:
                if attempt == self.max_retries:
                    logger.error(f"❌ 达到最大重试次数 ({self.max_retries})，抓取失败。")
                    raise
                logger.info(f"🔄 正在启动第 {attempt + 1} 次自动重试...")
                time.sleep(1)

    def transform_and_validate(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.info("⚙️ 启动业务规则引擎：执行考勤扣款折算与合规拦截...")
        payroll_payload = []
        
        for record in raw_data:
            status = "Approved"
            risk_flag = "正常"
            masked_name = mask_name(record['name']) # 日志输出必须脱敏
            
            # 风控规则 1：严重旷工拦截
            if record["absent_days"] >= 2:
                status = "Pending_Review"
                risk_flag = "严重旷工(阻断)"
                logger.warning(f"🛡️ 风控拦截：员工 {masked_name} 旷工 {record['absent_days']} 天，薪酬流转冻结！")
            
            # 风控规则 2：疲劳工作/超长加班审计
            elif record["overtime_hours"] > 18:
                status = "Pending_Review"
                risk_flag = "超长加班(复核)"
                logger.warning(f"🛡️ 风控拦截：员工 {masked_name} 加班 {record['overtime_hours']} 小时，触发合规复核！")

            payload_item = {
                "employee_id": record["emp_id"],
                "name": record["name"],  # 内部流转保留真实姓名
                "deduction_days": record["absent_days"],
                "bonus_hours": record["overtime_hours"],
                "payroll_status": status,
                "risk_flag": risk_flag
            }
            payroll_payload.append(payload_item)
            self.audit_records.append(payload_item)
            
        return payroll_payload

    def push_to_payroll(self, payload: List[Dict[str, Any]]):
        logger.info("📤 正在将标准化数据推送至【薪酬福利】暂存表...")
        time.sleep(1)
        valid_count = sum(1 for item in payload if item['payroll_status'] == 'Approved')
        logger.info(f"✅ 闭环完成！流转总数: {len(payload)} | 自动放行: {valid_count} | 人工复核: {len(payload)-valid_count}")

    def generate_audit_report(self):
        if not self.audit_records: return
        df = pd.DataFrame(self.audit_records)
        report_name = f"HCM_API_对账审计单_{datetime.now().strftime('%Y%m%d')}.xlsx"
        df.to_excel(report_name, index=False)
        logger.info(f"📊 业务审计对账单已生成，供 HR 专员复核：{report_name}")

# ==========================================
# 3. 生产环境启动入口
# ==========================================
if __name__ == "__main__":
    print("="*65)
    print("🚀 HCM Enterprise Data Integration Hub (最终版)")
    print("="*65)
    
    engine = HCMIntegrationEngine()
    try:
        token = engine.get_access_token()
        raw_data = engine.fetch_attendance_data(token)
        payload = engine.transform_and_validate(raw_data)
        engine.push_to_payroll(payload)
        engine.generate_audit_report()
    except Exception as e:
        logger.critical("🚨 系统发生不可恢复异常，自动化任务已中止！")