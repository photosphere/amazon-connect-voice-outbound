import streamlit as st
import boto3

# 初始化页面配置
st.set_page_config(page_title="语音外呼Demo", page_icon="📞")

# 设置页面标题
st.title("语音外呼Demo")

# 外呼语音通话函数
def start_outbound_voice_call(
    phone_number,
    user_name,
    connect_instance_id,
    contact_flow_id,
    source_phone_number=None
):
    try:
        # 初始化 Amazon Connect 客户端
        connect_client = boto3.client('connect')
        
        # 准备默认属性
        attributes = {'UserName': user_name, "LanguageCode": 'zh_CN'}
        
        # 准备 API 调用参数
        params = {
            'DestinationPhoneNumber': phone_number,
            'ContactFlowId': contact_flow_id,
            'InstanceId': connect_instance_id,
            'Attributes': attributes
        }
        
        # 添加可选参数（如果提供）
        if source_phone_number:
            params['SourcePhoneNumber'] = source_phone_number
        
        # 发起外呼电话
        response = connect_client.start_outbound_voice_contact(**params)
        
        print(f"成功发起外呼电话到 {phone_number}，ContactId: {response['ContactId']}")
        return response
        
    except Exception as e:
        print(f"发生未预期的错误: {str(e)}")
        raise

# 更新Lambda函数环境变量的函数
def update_lambda_env_var(prompt_content, lambda_arn, env_var_name):
    """更新指定Lambda函数的环境变量"""
    try:
        lambda_client = boto3.client('lambda')
        
        # 获取当前函数配置
        response = lambda_client.get_function_configuration(FunctionName=lambda_arn)
        
        # 更新环境变量
        current_env = response.get('Environment', {}).get('Variables', {})
        current_env[env_var_name] = prompt_content
        
        # 更新函数配置
        lambda_client.update_function_configuration(
            FunctionName=lambda_arn,
            Environment={'Variables': current_env}
        )
        
        return True
    except Exception as e:
        st.error(f"更新Lambda环境变量失败: {str(e)}")
        return False

# 创建表单
with st.form("outbound_form"):
    # 用户名称输入
    user_name = st.text_input("请输入用户名称", 
                             value="康先生",
                             max_chars=50)
    # 手机号码输入
    phone_number = st.text_input("请输入手机号码", 
                                placeholder="+12285332612",
                                value="+12285332612",
                                max_chars=12)
    
    # 提示词输入
    prompt_content = st.text_area("请输入提示词", 
                                 placeholder="请输入您的提示词内容...",
                                 height=330,value="你是一个信用卡还款提醒中心的AI助手，正在进行外呼服务。请按照以下流程与客户进行对话：确认客户身份（仅需确认是否为持卡人本人，无需获取敏感个人信息），告知本次通话的目的是提醒信用卡还款核心流程 还款意愿询问 礼貌提醒客户信用卡有一笔金额5000元2025年8月4日即将到期的账单，询问客户是否能够按时完成还款，处理客户回应。如客户表示能按时还款：表示感谢，提醒还款日期，简要说明还款渠道。如客户表示无法按时还款，表示理解并询问是否遇到还款困难，清晰提供三个选项：申请延后还款、转人工客服处理、或其他帮助。延后还款处理：如客户选择申请延后还款，询问客户需要延后的具体时间（几天或几周），根据客户回答提供相应的延期方案，说明延期可能产生的影响（如额外费用、记录等）对话指南。 保持语气专业、友善且有耐心 不对客户的还款能力做评判，尊重客户隐私，不过度询问财务困难的具体原因。避免使用威胁性或过于强硬的语言，提供清晰的选项和建议，整个交流过程中保持尊重和理解。结束语：感谢客户的时间和配合，最后询问客户是否还有其他问题。 礼貌道别请根据以上指引，与客户进行信用卡还款催收的对话，注意根据客户的不同回应灵活调整交流策略。每次回答的字数控制在150字以内，确保信息清晰易懂。不要回答跟信用卡还款不相关的问题。不要给初跟信用卡还款不相关的建议。",max_chars=2000)
    
    # 配置项折叠
    with st.expander("配置项", expanded=False):
        connect_instance_id = st.text_input("Connect实例ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",value="b7e4b4ed-1bdf-4b14-b624-d9328f08725a")
        contact_flow_id = st.text_input("联系流ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",value="bc57a009-89fd-424f-add6-c1f8fee2464d")
        source_phone_number = st.text_input("源电话号码（可选）", placeholder="+1234567890",value="+13072633584")
        lambda_arn = st.text_input("Lambda函数ARN", placeholder="arn:aws:lambda:region:account:function:function-name",value="arn:aws:lambda:us-east-1:991727053196:function:StartOutboundVoice_Claude_Haiku")
        env_var_name = st.text_input("环境变量名", placeholder="PROMPT_CONTENT",value="Prompt")
    
    # 外呼按钮
    if st.form_submit_button("外呼"):
        if not user_name.strip():
            st.error("请输入用户名称")
        elif not phone_number or len(phone_number) != 12:
            st.error("请输入有效的手机号码")
        elif not prompt_content.strip():
            st.error("请输入提示词内容")
        elif not connect_instance_id:
            st.error("请输入Connect实例ID")
        elif not contact_flow_id:
            st.error("请输入联系流ID")
        else:
            try:
                # 如果提供了Lambda配置，先更新环境变量
                if lambda_arn and env_var_name:
                    update_lambda_env_var(prompt_content, lambda_arn, env_var_name)
                
                response = start_outbound_voice_call(
                    phone_number=phone_number,
                    user_name=user_name,
                    connect_instance_id=connect_instance_id,
                    contact_flow_id=contact_flow_id,
                    source_phone_number=source_phone_number if source_phone_number else None
                )
                st.success(f"外呼成功！ContactId: {response['ContactId']}")
            except Exception as e:
                st.error(f"外呼失败: {str(e)}")
