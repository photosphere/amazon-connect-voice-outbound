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
        attributes = {'UserName': user_name, "Language": 'ZH'}
        
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
    
    # 配置项折叠
    with st.expander("配置项", expanded=False):
        connect_instance_id = st.text_input("Connect实例ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",value="b7e4b4ed-1bdf-4b14-b624-d9328f08725a")
        contact_flow_id = st.text_input("联系流ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",value="9168f50a-d81e-4060-a2cb-a127fe3d9198")
        source_phone_number = st.text_input("源电话号码（可选）", placeholder="+1234567890",value="+13072633584")
    
    # 外呼按钮
    if st.form_submit_button("外呼"):
        if not user_name.strip():
            st.error("请输入用户名称")
        elif not phone_number or len(phone_number) != 12:
            st.error("请输入有效的手机号码")
        elif not connect_instance_id:
            st.error("请输入Connect实例ID")
        elif not contact_flow_id:
            st.error("请输入联系流ID")
        else:
            try:
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