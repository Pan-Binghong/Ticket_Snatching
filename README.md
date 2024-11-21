# 上海天文馆自助抢票爬虫脚本

## 获取场馆信息
https://ticket.sstm.org.cn/vendor/common/getStadiums2.xhtml

1. 上海科技馆
2. 上海自然博物馆
3. 上海天文馆

https://ticket.sstm.org.cn/vendor/member/interesttag/getList.xhtml

https://ticket.sstm.org.cn//vendor/common/getMembershipEntryOpenstatus.xhtml

https://ticket.sstm.org.cn/vendor/openapi/openlogin/wxAutoLogin.xhtml

- 勾选阅读并同意后显示的所有信息

https://ticket.sstm.org.cn/vendor/common/getServerTime.xhtml

GET /vendor/reserve/getCloseDays.xhtml?stadiumId=69001&start=2024-11-12&sstCode=ssmtifri&appId=wx1d7ddce169710ba7 HTTP/1.1

https://ticket.sstm.org.cn/vendor/reserve/getReservedateListByStadiumId.xhtml
{
	"errcode": "0000",
	"data": {
		"startdate": "2024-11-12",
		"resultList": [{
			"reservedate": "2024-11-12",
			"visitorsnum": 3000,
			"usednum": null,
			"avaiablenum": null
		}, {
			"reservedate": "2024-11-13",
			"visitorsnum": 3000,
			"usednum": null,
			"avaiablenum": null
		}, {
			"reservedate": "2024-11-14",
			"visitorsnum": 3000,
			"usednum": null,
			"avaiablenum": null
		}],
		"enddate": "2024-11-15"
	},
	"success": true
}

URL	https://ticket.sstm.org.cn/vendor/reserve/getReservePeriodListByDate.xhtml
{
	"errcode": "0000",
	"data": {
		"reservePeriodList": [{
			"id": 63854,
			"week": 4,
			"status": "Y",
			"addtime": "2024-10-19 15:36:39",
			"updatetime": "2024-11-07 13:21:28",
			"visitorsnum": 1250,
			"starttime": "2024-11-14 09:30:00",
			"endtime": "2024-11-14 12:30:00",
			"reservedate": "2024-11-14",
			"stadiumId": 69001,
			"onlineSupport": "Y",
			"teamsnum": 0,
			"avaiablenum": 655,
			"avaiable": "Y",
			"availableNum": 655,
			"available": "Y"
		}, {
			"id": 63855,
			"week": 4,
			"status": "Y",
			"addtime": "2024-10-19 15:36:39",
			"updatetime": "2024-11-07 13:21:32",
			"visitorsnum": 1750,
			"starttime": "2024-11-14 12:30:00",
			"endtime": "2024-11-14 15:00:00",
			"reservedate": "2024-11-14",
			"stadiumId": 69001,
			"onlineSupport": "Y",
			"teamsnum": 0,
			"avaiablenum": 1542,
			"avaiable": "Y",
			"availableNum": 1542,
			"available": "Y"
		}]
	},
	"success": true
}

URL	https://ticket.sstm.org.cn/vendor/reserve/getScheduleListByReservePeriodId.xhtml
{
	"data": [{
		"id": 61038,
		"category": "visitor",
		"addtime": "2021-07-11 19:30:16",
		"updatetime": "2024-05-15 10:55:22",
		"available": "Y",
		"active": "Y",
		"cnName": "成人网售票",
		"tickettype": "normal",
		"stadiumId": 69001,
		"showPrice": 30.0,
		"venueId": 68001,
		"hasRights": "Y",
		"supportRefund": "Y",
		"checkcard": "M",
		"discountType": "normal",
		"maxChangeNum": 0,
		"sortNum": 1
	}, {
		"id": 61039,
		"category": "visitor",
		"addtime": "2021-07-11 19:37:30",
		"updatetime": "2024-05-15 10:55:40",
		"remark": "适用范围：1.3米以上及6周岁以上儿童、全日制大学本科及以下学历学生，检票时须出示本人学生证。",
		"available": "Y",
		"active": "Y",
		"cnName": "学生网售票",
		"tickettype": "student",
		"stadiumId": 69001,
		"showPrice": 15.0,
		"venueId": 68001,
		"hasRights": "Y",
		"supportRefund": "Y",
		"checkcard": "M",
		"discountType": "student",
		"maxChangeNum": 0,
		"sortNum": 2
	}, {
		"id": 61040,
		"category": "visitor",
		"addtime": "2021-07-11 19:47:29",
		"updatetime": "2024-05-15 10:55:55",
		"remark": "适用范围：60-69周岁的老年人，检票时须出示本人有效身份证件。",
		"available": "Y",
		"active": "Y",
		"cnName": "老年网售票",
		"tickettype": "old",
		"stadiumId": 69001,
		"showPrice": 25.0,
		"venueId": 68001,
		"hasRights": "Y",
		"supportRefund": "Y",
		"checkcard": "M",
		"discountType": "old",
		"maxChangeNum": 0,
		"sortNum": 3
	}, {
		"id": 61041,
		"category": "visitor",
		"addtime": "2021-07-11 19:49:01",
		"updatetime": "2022-09-13 19:40:42",
		"remark": "适用范围：现役军人的配偶、不能独立生活的成年子女、父母（扶养人），检票时须出示本人相关身份证明。",
		"available": "Y",
		"active": "Y",
		"cnName": "现役军人家属网售票",
		"tickettype": "militaryFamilies",
		"stadiumId": 69001,
		"showPrice": 25.0,
		"venueId": 68001,
		"hasRights": "Y",
		"supportRefund": "Y",
		"checkcard": "M",
		"discountType": "normal",
		"maxChangeNum": 0,
		"sortNum": 4
	}, {
		"id": 61042,
		"category": "visitor",
		"addtime": "2021-07-11 19:54:29",
		"updatetime": "2024-09-01 14:09:58",
		"remark": " 适用范围：1.3 米（含）以下或 6 周岁（含）以下的儿童，须由购票监护人陪同入馆。70 周岁（含）以上老年人、离休干部、现役军人、军队文职人员、烈士遗属、因公牺牲军人遗属、病故军人遗属、残疾人，在职、退休、残疾消防救援人员（含政府专职消防员）和消防救援院校学员、国家消防综合性救援人员，在职公安民警。检票时须出示本人有效身份证件。",
		"available": "Y",
		"active": "Y",
		"cnName": "免费人群参观票",
		"tickettype": "free",
		"stadiumId": 69001,
		"showPrice": 0.0,
		"venueId": 68001,
		"hasRights": "Y",
		"supportRefund": "Y",
		"checkcard": "M",
		"discountType": "extraCertType",
		"maxChangeNum": 0,
		"sortNum": 8
	}],
	"success": true
}

https://ticket.sstm.org.cn/vendor/reserve/getScheduleListByReservePeriodId.xhtml
{
	"data": [{
		"id": 61038,
		"category": "visitor",
		"addtime": "2021-07-11 19:30:16",
		"updatetime": "2024-05-15 10:55:22",
		"available": "Y",
		"active": "Y",
		"cnName": "成人网售票",
		"tickettype": "normal",
		"stadiumId": 69001,
		"showPrice": 30.0,
		"venueId": 68001,
		"hasRights": "Y",
		"supportRefund": "Y",
		"checkcard": "M",
		"discountType": "normal",
		"maxChangeNum": 0,
		"sortNum": 1
	}, {
		"id": 61039,
		"category": "visitor",
		"addtime": "2021-07-11 19:37:30",
		"updatetime": "2024-05-15 10:55:40",
		"remark": "适用范围：1.3米以上及6周岁以上儿童、全日制大学本科及以下学历学生，检票时须出示本人学生证。",
		"available": "Y",
		"active": "Y",
		"cnName": "学生网售票",
		"tickettype": "student",
		"stadiumId": 69001,
		"showPrice": 15.0,
		"venueId": 68001,
		"hasRights": "Y",
		"supportRefund": "Y",
		"checkcard": "M",
		"discountType": "student",
		"maxChangeNum": 0,
		"sortNum": 2
	}, {
		"id": 61040,
		"category": "visitor",
		"addtime": "2021-07-11 19:47:29",
		"updatetime": "2024-05-15 10:55:55",
		"remark": "适用范围：60-69周岁的老年人，检票时须出示本人有效身份证件。",
		"available": "Y",
		"active": "Y",
		"cnName": "老年网售票",
		"tickettype": "old",
		"stadiumId": 69001,
		"showPrice": 25.0,
		"venueId": 68001,
		"hasRights": "Y",
		"supportRefund": "Y",
		"checkcard": "M",
		"discountType": "old",
		"maxChangeNum": 0,
		"sortNum": 3
	}, {
		"id": 61041,
		"category": "visitor",
		"addtime": "2021-07-11 19:49:01",
		"updatetime": "2022-09-13 19:40:42",
		"remark": "适用范围：现役军人的配偶、不能独立生活的成年子女、父母（扶养人），检票时须出示本人相关身份证明。",
		"available": "Y",
		"active": "Y",
		"cnName": "现役军人家属网售票",
		"tickettype": "militaryFamilies",
		"stadiumId": 69001,
		"showPrice": 25.0,
		"venueId": 68001,
		"hasRights": "Y",
		"supportRefund": "Y",
		"checkcard": "M",
		"discountType": "normal",
		"maxChangeNum": 0,
		"sortNum": 4
	}, {
		"id": 61042,
		"category": "visitor",
		"addtime": "2021-07-11 19:54:29",
		"updatetime": "2024-09-01 14:09:58",
		"remark": " 适用范围：1.3 米（含）以下或 6 周岁（含）以下的儿童，须由购票监护人陪同入馆。70 周岁（含）以上老年人、离休干部、现役军人、军队文职人员、烈士遗属、因公牺牲军人遗属、病故军人遗属、残疾人，在职、退休、残疾消防救援人员（含政府专职消防员）和消防救援院校学员、国家消防综合性救援人员，在职公安民警。检票时须出示本人有效身份证件。",
		"available": "Y",
		"active": "Y",
		"cnName": "免费人群参观票",
		"tickettype": "free",
		"stadiumId": 69001,
		"showPrice": 0.0,
		"venueId": 68001,
		"hasRights": "Y",
		"supportRefund": "Y",
		"checkcard": "M",
		"discountType": "extraCertType",
		"maxChangeNum": 0,
		"sortNum": 8
	}],
	"success": true
}

- 勾选阅读退票协议
https://ticket.sstm.org.cn/vendor/cautious/getByStadiumIdAndType.xhtml
{
	"errcode": "0000",
	"data": "由于场馆每日限量售票，请观众理性购票及退票，共同维护良好秩序。\n1、如确需退票，请在参观日前一天23:30前在原购票平台申请。\n2、如遇特殊情况，请拨打咨询电话(021)50685563、50908563，经馆方审核通过后票款将在10个工作日通过原支付渠道退返。\n3、退票时，同一证件号对应的“参观票+电影票”须同时办理退票申请。\n\n",
	"success": true
}


URL	https://ticket.sstm.org.cn/vendor/member/captchaRequire.xhtml?stadiumId=69001&appId=wx1d7ddce169710ba7
{
	"data": "Y",
	"success": true
}

https://ticket.sstm.org.cn/vendor/member/getMemberTicketInfoList.xhtml
{
	"errcode": "0000",
	"data": {
		"resultList": [{
			"id": 15982800,
			"memberId": 6619106,
			"realname": "潘秉宏",
			"certificateType": "idcard",
			"certificateNo": "620105199902220015",
			"certificateEncode": "44261FB36B9BDB49F009C560B02894B6FBD6C5ED58365B7F",
			"certificateMd5": "5eafebb1e0d9f45263224b8158615205",
			"tag": null,
			"apiLivenessRecognitionTimes": 0,
			"remainLivenessRecognitionTimes": 3,
			"verifyPhotoUrl": null,
			"verifyStatus": "new",
			"verifyMethod": "online",
			"verifyTime": null,
			"verifyAdditionInfo": null,
			"verifiable": "dual",
			"addtime": "2024-11-12 15:47:14",
			"updatetime": "2024-11-12 15:47:14",
			"youngFlag": "N"
		}]
	},
	"success": true
}

URL	https://ticket.sstm.org.cn/vendor/member/memberInfo.xhtml
{
	"data": {
		"errcode": null,
		"msg": null,
		"data": {
			"orderReqTime": 1731400211742,
			"openId": "oY9oQ5D2tZLqEOoM7zundFGcMabk",
			"contactNumber": "5992ce0ec5c4da67f7f01e5e460b8bfe"
		},
		"success": false
	},
	"success": true
}

URL	https://ticket.sstm.org.cn/vendor/member/getPaymentGatewayList.xhtml
{
	"data": [{
		"gatewayName": "浦发微信",
		"merchantCode": "spdbprod",
		"gatewayCode": "spdbBankPay:appWx",
		"paybank": "appWx",
		"useable": true,
		"name": "浦发微信"
	}],
	"success": true
}

URL	https://ticket.sstm.org.cn/vendor/reserve/getReserveVisitorDaysAndOpenMinutesByStadiumId.xhtml
{
	"errcode": "0000",
	"data": {
		"delaySeconds": 0,
		"delayMinutes": 0,
		"openBuyTime": 1731375000000,
		"openMinutes": 570,
		"preSaleDay": 3
	},
	"success": true
}

URL	https://rce.tencentrio.com/sstmticket/sam/vendor/member/order/payOrder.xhtml
{
	"msg": "预订失败!",
	"errcode": "1101",
	"data": null,
	"success": false
}


# 1. 创建虚拟环境（推荐）
python -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python main.py