import streamlit as st
import boto3
import json
import zipfile
import os
import subprocess
import tempfile
from pathlib import Path

st.set_page_config(page_title="Amazon Connect自动化部署", page_icon="🚀")
st.title("Amazon Connect自动化部署")

def create_cdk_app(aws_access_key, aws_secret_key, region, connect_instance_id, stack_name):
    """创建CDK应用代码"""
    cdk_code = f'''import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_connect as connect,
    aws_lex as lex,
)
from constructs import Construct
import json

class VoiceOutboundStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Lambda执行角色
        lambda_role = iam.Role(
            self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonConnect_FullAccess")
            ]
        )
        
        # Lambda函数
        lambda_function = _lambda.Function(
            self, "VoiceOutboundLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("voice_outbound_llm_lambda.zip"),
            role=lambda_role,
            timeout=cdk.Duration.minutes(5)
        )
        
        # 联系流 - 仅在文件存在时创建
        try:
            with open("voice_outbound_llm_flow.json", "r") as f:
                flow_content = json.load(f)
            
            contact_flow = connect.CfnContactFlow(
                self, "VoiceOutboundFlow",
                instance_arn=f"arn:aws:connect:{region}:{{self.account}}:instance/{connect_instance_id}",
                name="VoiceOutboundLLMFlow",
                type="CONTACT_FLOW",
                content=json.dumps(flow_content)
            )
        except FileNotFoundError:
            print("voice_outbound_llm_flow.json not found, skipping contact flow creation")

app = cdk.App()
VoiceOutboundStack(app, "{stack_name}")
app.synth()
'''
    return cdk_code

def deploy_resources(aws_access_key, aws_secret_key, region, connect_instance_id, stack_name, use_default_credentials=False):
    """部署AWS资源"""
    try:
        # 设置AWS凭证
        if not use_default_credentials:
            os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key
            os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_key
        os.environ['AWS_DEFAULT_REGION'] = region
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建CDK项目结构
            app_py = os.path.join(temp_dir, "app.py")
            with open(app_py, "w") as f:
                f.write(create_cdk_app(aws_access_key, aws_secret_key, region, connect_instance_id, stack_name))
            
            # 复制必要文件
            current_dir = Path(__file__).parent
            for file_name in ["voice_outbound_llm_flow.json", "voice_outbound_llm_lambda.zip", "voice_outbound_llm_lex.zip"]:
                src = current_dir / file_name
                if src.exists():
                    dst = os.path.join(temp_dir, file_name)
                    if file_name.endswith('.zip'):
                        import shutil
                        shutil.copy2(src, dst)
                    else:
                        with open(src, 'r') as f_src, open(dst, 'w') as f_dst:
                            f_dst.write(f_src.read())
            
            # 创建cdk.json
            cdk_json = os.path.join(temp_dir, "cdk.json")
            with open(cdk_json, "w") as f:
                json.dump({
                    "app": "python app.py",
                    "watch": {
                        "include": ["**"],
                        "exclude": ["README.md", "cdk*.json", "requirements*.txt", "source.bat", "**/__pycache__", "**/*.pyc"]
                    },
                    "context": {
                        "@aws-cdk/aws-lambda:recognizeLayerVersion": True,
                        "@aws-cdk/core:checkSecretUsage": True,
                        "@aws-cdk/core:target-partitions": ["aws", "aws-cn"]
                    }
                }, f, indent=2)
            
            # 创建requirements.txt
            requirements = os.path.join(temp_dir, "requirements.txt")
            with open(requirements, "w") as f:
                f.write("aws-cdk-lib>=2.0.0\nconstructs>=10.0.0")
            
            # 安装依赖
            subprocess.run(["pip", "install", "-r", "requirements.txt"], cwd=temp_dir, check=True)
            
            # Bootstrap CDK环境
            bootstrap_result = subprocess.run(["cdk", "bootstrap"], 
                                            cwd=temp_dir, capture_output=True, text=True)
            if bootstrap_result.returncode != 0:
                return False, bootstrap_result.stdout, f"Bootstrap失败: {bootstrap_result.stderr}"
            
            # 部署
            result = subprocess.run(["cdk", "deploy", "--require-approval", "never"], 
                                  cwd=temp_dir, capture_output=True, text=True)
            
            return result.returncode == 0, result.stdout, result.stderr
            
    except Exception as e:
        return False, "", str(e)

# Streamlit界面
with st.form("deploy_form"):
    st.subheader("AWS配置")
    use_default_credentials = st.checkbox("使用默认AWS凭证", help="使用本地配置的AWS凭证（~/.aws/credentials）")
    
    if not use_default_credentials:
        aws_access_key = st.text_input("AWS Access Key ID", type="password")
        aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
    else:
        aws_access_key = ""
        aws_secret_key = ""
    
    region = st.selectbox("AWS Region", ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"])
    
    st.subheader("Amazon Connect配置")
    connect_instance_id = st.text_input("Amazon Connect实例ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    stack_name = st.text_input("Stack名称", value="VoiceOutboundStack", placeholder="输入CDK Stack名称")
    
    if st.form_submit_button("开始部署"):
        if use_default_credentials:
            required_fields = [connect_instance_id, stack_name]
        else:
            required_fields = [aws_access_key, aws_secret_key, connect_instance_id, stack_name]
        
        if not all(required_fields):
            st.error("请填写所有必填字段")
        else:
            with st.spinner("正在部署资源..."):
                success, stdout, stderr = deploy_resources(aws_access_key, aws_secret_key, region, connect_instance_id, stack_name, use_default_credentials)
                
                if success:
                    st.success("部署成功！")
                    if stdout:
                        st.text_area("部署输出", stdout, height=200)
                else:
                    st.error("部署失败")
                    if stderr:
                        st.text_area("错误信息", stderr, height=200)

# 文件检查状态
st.subheader("部署文件状态")
current_dir = Path(__file__).parent
required_files = ["voice_outbound_llm_flow.json", "voice_outbound_llm_lambda.zip", "voice_outbound_llm_lex.zip"]

for file_name in required_files:
    file_path = current_dir / file_name
    if file_path.exists():
        st.success(f"✅ {file_name}")
    else:
        st.error(f"❌ {file_name} - 文件不存在")