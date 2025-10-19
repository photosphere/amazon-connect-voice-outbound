import streamlit as st
import boto3
import pandas as pd
from datetime import datetime, timezone

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
        attributes = {'UserName': user_name}
        
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
                             value="TestUser",
                             max_chars=50)
    
    # 手机号码输入
    # connect-us-1 MX number
    phone_number = st.text_input("请输入手机号码", 
                                placeholder="+12285332612",
                                value="+525593312700",
                                max_chars=13)
    
    # 配置项折叠
    # connect-us-finance.my.connect.aws
    # DiDi DebtCollection Voicemail Flow
    with st.expander("配置项", expanded=False):
        connect_instance_id = st.text_input("Connect实例ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",value="31d131ac-b62a-4c16-a720-1154c8ddb841")
        contact_flow_id = st.text_input("联系流ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",value="e5b39750-8132-44e0-adfb-be0ed7eb2d51")
        source_phone_number = st.text_input("源电话号码（可选）", placeholder="+1234567890",value="+525552321084")
        now = datetime.now(timezone.utc)
        default_s3_path = f"s3://financetest0514/ctr-base/year={now.year}/month={now.month}/day={now.day}/"
        ctr_s3_bucket = st.text_input("通话记录存储桶", value=default_s3_path)
    
    # 外呼按钮
    if st.form_submit_button("外呼"):
        if not user_name.strip():
            st.error("请输入用户名称")
        elif not phone_number or len(phone_number) > 13:
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
                st.success("外呼成功！")
                start_time_utc = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                contact_id = response['ContactId']
                
                if 'df' not in st.session_state:
                    st.session_state.df = pd.DataFrame({
                        "Name": ["ContactId", "StartTime"],
                        "Value": [contact_id, start_time_utc]
                    })
                    st.session_state.contact_id = contact_id
                    st.session_state.connect_instance_id = connect_instance_id
                
                st.dataframe(st.session_state.df, hide_index=True)
            except Exception as e:
                st.error(f"外呼失败: {str(e)}")

if st.button("更新"):
    if 'contact_id' in st.session_state:
        try:
            connect_client = boto3.client('connect')
            response = connect_client.describe_contact(
                InstanceId=st.session_state.connect_instance_id,
                ContactId=st.session_state.contact_id
            )
            
            st.write(response)
            
            contact = response['Contact']
            
            names = ["ContactId", "StartTime"]
            values = [st.session_state.contact_id, st.session_state.df.iloc[1]['Value']]
            
            if 'InitiationTimestamp' in contact:
                names.append("InitiationTimestamp")
                values.append(contact['InitiationTimestamp'].strftime('%Y-%m-%dT%H:%M:%SZ'))
            
            if 'ConnectedToSystemTimestamp' in contact:
                names.append("ConnectedToSystemTimestamp")
                values.append(contact['ConnectedToSystemTimestamp'].strftime('%Y-%m-%dT%H:%M:%SZ'))
            
            if 'AgentInfo' in contact and 'ConnectedToAgentTimestamp' in contact['AgentInfo']:
                names.append("ConnectedToAgentTimestamp")
                values.append(contact['AgentInfo']['ConnectedToAgentTimestamp'].strftime('%Y-%m-%dT%H:%M:%SZ'))
            
            if 'DisconnectTimestamp' in contact:
                names.append("DisconnectTimestamp")
                values.append(contact['DisconnectTimestamp'].strftime('%Y-%m-%dT%H:%M:%SZ'))
            
            if 'DisconnectDetails' in contact and 'PotentialDisconnectIssue' in contact['DisconnectDetails']:
                names.append("DisconnectReason")
                values.append(contact['DisconnectDetails']['PotentialDisconnectIssue'])
            
            if 'Attributes' in contact and 'amd_result' in contact['Attributes']:
                names.append("amd_result")
                values.append(contact['Attributes']['amd_result'])
            
            st.session_state.df = pd.DataFrame({"Name": names, "Value": values})
            st.success("记录已更新！")
            st.dataframe(st.session_state.df, hide_index=True)
        except Exception as e:
            st.error(f"更新失败: {str(e)}")
    else:
        st.warning("请先执行外呼操作")