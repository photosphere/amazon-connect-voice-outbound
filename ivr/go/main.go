// Command voice_outbound_ivr 通过 AWS SDK for Go v2 调用 Amazon Connect 的
// StartOutboundVoiceContact API 发起一通外呼电话。
//
// 参考文档:
//   https://pkg.go.dev/github.com/aws/aws-sdk-go-v2/service/connect#Client.StartOutboundVoiceContact
//
// 参数取值与同目录下 voice_outbound_ivr.py 中的默认值保持一致，可通过命令行
// 标志覆盖。
package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/connect"
)

func main() {
	var (
		phoneNumber       string
		userName          string
		instanceID        string
		contactFlowID     string
		sourcePhoneNumber string
		language          string
		region            string
	)

	flag.StringVar(&phoneNumber, "phone-number", "+12285332612", "目标电话号码 (E.164 格式), 对应 DestinationPhoneNumber")
	flag.StringVar(&userName, "user-name", "康先生", "用户名称, 作为 Attributes.UserName 传入联系流")
	flag.StringVar(&instanceID, "instance-id", "b7e4b4ed-1bdf-4b14-b624-d9328f08725a", "Amazon Connect 实例 ID, 对应 InstanceId")
	flag.StringVar(&contactFlowID, "contact-flow-id", "9168f50a-d81e-4060-a2cb-a127fe3d9198", "联系流 ID, 对应 ContactFlowId")
	flag.StringVar(&sourcePhoneNumber, "source-phone-number", "+13072633584", "主叫号码 (可选, 留空则不传), 对应 SourcePhoneNumber")
	flag.StringVar(&language, "language", "ZH", "Attributes.Language 的值")
	flag.StringVar(&region, "region", "", "AWS 区域 (留空则使用环境变量或默认配置)")
	flag.Parse()

	if phoneNumber == "" || instanceID == "" || contactFlowID == "" {
		log.Println("phone-number, instance-id, contact-flow-id 均为必填")
		flag.Usage()
		os.Exit(2)
	}

	ctx := context.Background()

	// 加载默认 AWS 配置 (环境变量, ~/.aws/credentials, ~/.aws/config 等).
	loadOpts := []func(*config.LoadOptions) error{}
	if region != "" {
		loadOpts = append(loadOpts, config.WithRegion(region))
	}
	cfg, err := config.LoadDefaultConfig(ctx, loadOpts...)
	if err != nil {
		log.Fatalf("加载 AWS 配置失败: %v", err)
	}

	client := connect.NewFromConfig(cfg)

	input := &connect.StartOutboundVoiceContactInput{
		DestinationPhoneNumber: aws.String(phoneNumber),
		ContactFlowId:          aws.String(contactFlowID),
		InstanceId:             aws.String(instanceID),
		Attributes: map[string]string{
			"UserName": userName,
			"Language": language,
		},
	}

	if sourcePhoneNumber != "" {
		input.SourcePhoneNumber = aws.String(sourcePhoneNumber)
	}

	resp, err := client.StartOutboundVoiceContact(ctx, input)
	if err != nil {
		log.Fatalf("外呼失败: %v", err)
	}

	fmt.Printf("成功发起外呼电话到 %s, ContactId: %s\n", phoneNumber, aws.ToString(resp.ContactId))
}
