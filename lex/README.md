# amazon-connect-voice-outbound

### Automatic Outbound with custom message

#### voice_outbound_ivr.py
<img width="763" height="445" alt="Image" src="https://github.com/user-attachments/assets/7316f6b4-3692-414d-a2dc-bc04c8e0dc53" />

#### voice_outbound_ivr_flow.json
<img width="1523" height="660" alt="Image" src="https://github.com/user-attachments/assets/d7b0a35e-bb64-4d32-b5de-47ef15ad18b9" />

---

### Go CLI: `go/main.go`

使用 [AWS SDK for Go v2](https://pkg.go.dev/github.com/aws/aws-sdk-go-v2/service/connect#Client.StartOutboundVoiceContact)
的 `connect.Client.StartOutboundVoiceContact` 发起外呼，参数默认值与
`voice_outbound_ivr.py` 中保持一致。

#### 目录结构

```
ivr/
└── go/
    ├── go.mod
    └── main.go
```

#### 准备依赖

首次使用需在 `ivr/go/` 目录下拉取依赖：

```bash
cd ivr/go
go mod tidy
```

`go mod tidy` 会自动添加以下模块：

- `github.com/aws/aws-sdk-go-v2`
- `github.com/aws/aws-sdk-go-v2/config`
- `github.com/aws/aws-sdk-go-v2/service/connect`

#### 配置 AWS 凭证

程序使用默认凭证链（环境变量、`~/.aws/credentials`、IAM Role 等）。可通过以下任一方式提供：

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1            # 或通过 -region 标志指定
# 或者
aws configure
```

调用方需具备 `connect:StartOutboundVoiceContact` 权限。

#### 运行

使用默认参数（与 Python 版一致）：

```bash
go run . \
  -phone-number=+12285332612 \
  -user-name=康先生 \
  -instance-id=b7e4b4ed-1bdf-4b14-b624-d9328f08725a \
  -contact-flow-id=9168f50a-d81e-4060-a2cb-a127fe3d9198 \
  -source-phone-number=+13072633584 \
  -language=ZH \
  -region=us-east-1
```

或编译后执行：

```bash
go build -o voice-outbound .
./voice-outbound -phone-number=+12285332612
```

#### 命令行参数

| 标志 | 默认值 | 说明 | 对应 API 字段 |
| --- | --- | --- | --- |
| `-phone-number` | `+12285332612` | 目标号码 (E.164) | `DestinationPhoneNumber` |
| `-user-name` | `康先生` | 用户姓名，写入联系流属性 | `Attributes.UserName` |
| `-instance-id` | `b7e4b4ed-1bdf-4b14-b624-d9328f08725a` | Amazon Connect 实例 ID | `InstanceId` |
| `-contact-flow-id` | `9168f50a-d81e-4060-a2cb-a127fe3d9198` | 联系流 ID | `ContactFlowId` |
| `-source-phone-number` | `+13072633584` | 主叫号码（留空则不传） | `SourcePhoneNumber` |
| `-language` | `ZH` | 语种属性 | `Attributes.Language` |
| `-region` | _(空)_ | AWS 区域，留空则使用默认配置 | — |

#### 输出示例

```
成功发起外呼电话到 +12285332612, ContactId: 12345678-aaaa-bbbb-cccc-1234567890ab
```

---

### AWS CLI: `aws connect start-outbound-voice-contact`

直接通过 [AWS CLI](https://docs.aws.amazon.com/cli/latest/reference/connect/start-outbound-voice-contact.html)
发起外呼，参数取值与 `voice_outbound_ivr.py` 中保持一致。

#### 前置条件

- 已安装 [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)。
- 已配置具备 `connect:StartOutboundVoiceContact` 权限的凭证（`aws configure` 或环境变量）。
- AWS 区域设置为 Amazon Connect 实例所在区域，例如 `us-east-1`。

#### 命令示例

```bash
aws connect start-outbound-voice-contact \
  --region us-east-1 \
  --destination-phone-number "+12285332612" \
  --contact-flow-id "9168f50a-d81e-4060-a2cb-a127fe3d9198" \
  --instance-id "b7e4b4ed-1bdf-4b14-b624-d9328f08725a" \
  --source-phone-number "+13072633584" \
  --attributes UserName=康先生,Language=ZH
```

也可以将 `--attributes` 改为 JSON 形式（与 SDK 调用一致）：

```bash
aws connect start-outbound-voice-contact \
  --region us-east-1 \
  --destination-phone-number "+12285332612" \
  --contact-flow-id "9168f50a-d81e-4060-a2cb-a127fe3d9198" \
  --instance-id "b7e4b4ed-1bdf-4b14-b624-d9328f08725a" \
  --source-phone-number "+13072633584" \
  --attributes '{"UserName":"康先生","Language":"ZH"}'
```

> 提示：使用 `--client-token <UUID>` 可保证调用幂等，避免重复外呼。

#### 参数说明

| CLI 参数 | 取值 | 对应 API 字段 |
| --- | --- | --- |
| `--destination-phone-number` | `+12285332612` | `DestinationPhoneNumber` |
| `--contact-flow-id` | `9168f50a-d81e-4060-a2cb-a127fe3d9198` | `ContactFlowId` |
| `--instance-id` | `b7e4b4ed-1bdf-4b14-b624-d9328f08725a` | `InstanceId` |
| `--source-phone-number` | `+13072633584` | `SourcePhoneNumber` |
| `--attributes` | `UserName=康先生,Language=ZH` | `Attributes` |
| `--region` | `us-east-1` | — |

#### 返回示例

```json
{
    "ContactId": "12345678-aaaa-bbbb-cccc-1234567890ab"
}
```
