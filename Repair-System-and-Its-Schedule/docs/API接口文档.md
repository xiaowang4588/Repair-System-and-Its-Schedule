# 青果教务系统 API 接口文档

> 学校：重庆移通学院（綦江校区）
> 系统：青果教务管理系统
> 记录时间：2026-05-29
> 访问方式：通过 VPN 网关代理访问

---

## 1. 系统信息

| 项目 | 值 |
|------|-----|
| 教务系统基础地址 | `https://http-10-252-6-31-80.vpn.cqytxy.edu.cn` |
| VPN 网关地址 | `https://vpn.cqytxy.edu.cn` |
| 远程服务器 IP | `183.64.130.7:443` |
| Web 服务器 | Tengine |
| 前端框架 | jQuery + jqGrid |
| 页面类型 | SPA（单页应用），数据通过 AJAX 动态加载 |

---

## 2. 认证方式

### 2.1 VPN 网关认证

系统部署在学校内网，通过 VPN 网关代理访问。所有请求先经过 VPN 网关验证身份。

**认证流程**：
1. 用户访问教务系统 URL
2. VPN 网关检查请求中是否携带有效的 `webvpn-token`
3. 如果没有令牌或令牌过期，重定向到 VPN 登录页 `https://vpn.cqytxy.edu.cn`
4. 登录成功后，VPN 网关在 Cookie 中设置 `webvpn-token`（JWT 格式）

### 2.2 必需的 Cookie

| Cookie 名称 | 说明 | 示例 |
|-------------|------|------|
| `webvpn-token` | JWT 令牌，VPN 网关认证凭证，有效期很长（约1-2年） | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `JSESSIONID` | Java 会话 ID，教务系统内部会话标识 | `4547E4D5C5C0D6D979BB851268B7D799` |
| `route` | 负载均衡路由标识 | `455e33d3378116382c065d3a4b314a4e` |

### 2.3 如何获取 Cookie

1. 用浏览器打开教务系统并登录
2. 按 **F12** → **Application**（应用）→ **Cookies**
3. 复制 `webvpn-token` 和 `JSESSIONID` 的值

### 2.4 JWT 令牌结构（webvpn-token 解码后）

```json
{
  "userId": 20833,
  "userName": "2024214737",
  "authenticateExternalId": "yGrVwtUA",
  "authenticateType": 4,
  "authenticateExternalUserId": "2024214737",
  "salt": "194979648227051354",
  "needTriggerTFA": false,
  "needChangePwd": false,
  "sessionId": "",
  "exp": 1811578414,
  "iss": "webvpn"
}
```

- `exp: 1811578414` → 过期时间约为 **2027年9月**
- `userName` → 学号/工号
- `authenticateType: 4` → 认证类型

---

## 3. 空教室查询 API

### 3.1 请求信息

| 项目 | 值 |
|------|-----|
| **URL** | `POST /jwglxt/cdjy/cdjy_cxSfkfyuy.html?gnmkdm=N2155` |
| **完整地址** | `https://http-10-252-6-31-80.vpn.cqytxy.edu.cn/jwglxt/cdjy/cdjy_cxSfkfyuy.html?gnmkdm=N2155` |
| **请求方法** | `POST` |
| **Content-Type** | `application/x-www-form-urlencoded;charset=UTF-8` |
| **响应格式** | `application/json;charset=UTF-8` |
| **X-Requested-With** | `XMLHttpRequest`（标识为 AJAX 请求） |

### 3.2 请求参数（Form Data）

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| `doType` | string | 是 | 操作类型，固定值 `query` | `query` |
| `gnmkdm` | string | 是 | 功能模块代码，固定值 `N2155` | `N2155` |
| `xqh_id` | string | 是 | 校区 ID | `C67E548C4B4553FFE0530100007F06AD`（綦江校区） |
| `xnm` | string | 是 | 学年 | `2025`（表示 2025-2026 学年） |
| `xqm` | string | 是 | 学期 | `12`（春季学期）、`3`（秋季学期） |
| `cdlb_id` | string | 否 | 教室类别 ID | 空=全部、`010`=多媒体、`011`=办公室 |
| `cdejlb_id` | string | 否 | 教室二级类别 ID | 空=全部 |
| `qszws` | string | 否 | 起始座位数 | 空=不限 |
| `jszws` | string | 否 | 结束座位数 | 空=不限 |
| `cdmc` | string | 否 | 教室名称（模糊搜索） | `仁者楼` |
| `lh` | string | 否 | 楼号 | `003` |
| `jyfs` | string | 否 | 借用方式 | `0`（默认） |
| `cdjylx` | string | 否 | 教室借用类型 | 空 |
| `sfbhkc` | string | 否 | 是否包含课程 | 空=查询空教室 |
| `zcd` | string | 否 | 周次 | `7`（第7周） |
| `xqj` | string | 否 | 星期几 | `1`=周一、`2`=周二 ... `7`=周日 |
| `jcd` | string | 否 | 节次 | `1`=1-2节、`2`=3-4节、`3`=5-6节、`4`=7-8节、`5`=9-10节、`6`=11-12节 |
| `_search` | string | 是 | 是否搜索，固定值 `false` | `false` |
| `nd` | string | 是 | 时间戳（毫秒） | `1780044693328` |
| `queryModel.showCount` | string | 是 | 每页显示条数 | `15`（默认）、`500`（获取全部） |
| `queryModel.currentPage` | string | 是 | 当前页码 | `1` |
| `queryModel.sortName` | string | 是 | 排序字段 | `cdbh`（场地编号） |
| `queryModel.sortOrder` | string | 是 | 排序方向 | `asc`（升序） |
| `time` | string | 是 | 请求序号 | `2` |

### 3.3 响应数据结构

```json
{
    "currentPage": 1,
    "currentResult": 0,
    "entityOrField": false,
    "items": [
        {
            "cd_id": "00015",
            "cdbh": "00015",
            "cdlb_id": "010",
            "cdlbmc": "多媒体",
            "cdmc": "仁者楼402",
            "cdxqxx_id": "435D5E4BD9F063E4E0630100007FA2E7",
            "date": "二○二六年五月二十九日",
            "dateDigit": "2026年5月29日",
            "dateDigitSeparator": "2026-5-29",
            "day": "29",
            "jgpxzd": "1",
            "jxlmc": "仁者楼",
            "jzmj": "160",
            "kszws1": "60",
            "lh": "003",
            "listnav": "false",
            "localeKey": "zh_CN",
            "month": "5",
            "pageTotal": 0,
            "pageable": true,
            "queryModel": { ... },
            "rangeable": true,
            "row_id": "1",
            "sfybyy": "否",
            "totalResult": "264",
            "userModel": { ... },
            "xqh_id": "C67E548C4B4553FFE0530100007F06AD",
            "xqmc": "綦江校区",
            "year": "2026",
            "zws": "120"
        }
    ],
    "limit": 15,
    "offset": 0,
    "pageNo": 0,
    "pageSize": 15,
    "showCount": 15,
    "sortName": "cdbh ",
    "sortOrder": "asc",
    "sorts": [],
    "totalCount": 264,
    "totalPage": 18,
    "totalResult": 264
}
```

### 3.4 响应字段说明

**顶层字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `currentPage` | int | 当前页码 |
| `totalCount` | int | 总记录数 |
| `totalPage` | int | 总页数 |
| `totalResult` | int | 总结果数 |
| `items` | array | 教室数据数组 |

**items 数组中每个元素的字段**：

| 字段 | 类型 | 说明 | 示例值 |
|------|------|------|--------|
| `cd_id` | string | 场地 ID | `00015` |
| `cdbh` | string | 场地编号 | `00015` |
| `cdmc` | string | 教室名称 | `仁者楼402` |
| `cdlb_id` | string | 教室类别 ID | `010` |
| `cdlbmc` | string | 教室类别名称 | `多媒体`、`办公室`、`其他` |
| `jxlmc` | string | 教学楼名称 | `仁者楼`、`智者楼` |
| `lh` | string | 楼号 | `003` |
| `jzmj` | string | 建筑面积（平方米） | `160` |
| `kszws1` | string | 可使用座位数 | `60` |
| `zws` | string | 总座位数 | `120` |
| `sfybyy` | string | 是否有被预约 | `否` |
| `bz` | string | 备注 | `远景阶梯教室（无黑板）` |
| `xqh_id` | string | 校区 ID | `C67E548C4B4553FFE0530100007F06AD` |
| `xqmc` | string | 校区名称 | `綦江校区` |
| `cdxqxx_id` | string | 场地校区信息 ID | `435D5E4BD9F063E4E0630100007FA2E7` |

### 3.5 查询示例

**查询周一第5-6节的空教室（第7周）**：

```
POST /jwglxt/cdjy/cdjy_cxSfkfyuy.html?gnmkdm=N2155

doType=query
gnmkdm=N2155
xqh_id=C67E548C4B4553FFE0530100007F06AD
xnm=2025
xqm=12
zcd=7
xqj=1
jcd=3
queryModel.showCount=500
queryModel.currentPage=1
queryModel.sortName=cdbh
queryModel.sortOrder=asc
```

**查询结果**：返回 264 间教室（均为该时段的空教室）

---

## 4. 辅助接口

### 4.1 周次描述接口

| 项目 | 值 |
|------|-----|
| **URL** | `POST /jwglxt/pkglcommon/common_cxZcdesc.html?gnmkdm=N2155` |
| **说明** | 获取当前周次信息 |

### 4.2 节次描述接口

| 项目 | 值 |
|------|-----|
| **URL** | `POST /jwglxt/pkglcommon/common_cxJcdesc.html?gnmkdm=N2155` |
| **说明** | 获取节次时间描述信息 |

### 4.3 教室列表页面

| 项目 | 值 |
|------|-----|
| **URL** | `GET /jwglxt/cdjy/cdjy_cxKxcdlb.html?gnmkdm=N2155&layout=default` |
| **说明** | 空教室查询的前端页面（HTML） |

---

## 5. 请求头模板

```
POST /jwglxt/cdjy/cdjy_cxSfkfyuy.html?gnmkdm=N2155 HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: zh-CN,zh;q=0.9
Connection: keep-alive
Content-Type: application/x-www-form-urlencoded;charset=UTF-8
Cookie: JSESSIONID=xxxxx; webvpn-token=xxxxx; route=xxxxx
Host: http-10-252-6-31-80.vpn.cqytxy.edu.cn
Origin: https://http-10-252-6-31-80.vpn.cqytxy.edu.cn
Referer: https://http-10-252-6-31-80.vpn.cqytxy.edu.cn/jwglxt/cdjy/cdjy_cxKxcdlb.html?gnmkdm=N2155&layout=default
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

---

## 6. 已知信息与待确认项

### 已确认

- [x] API 地址和请求方法
- [x] 请求参数格式（Form Data）
- [x] 响应数据结构（JSON）
- [x] 认证方式（VPN 网关 + webvpn-token）
- [x] 分页机制（queryModel.showCount / queryModel.currentPage）
- [x] 教室数据字段含义
- [x] 校区 ID（綦江校区）
- [x] 学期编码（12=春季，3=秋季）

### 待确认

- [ ] **课表查询 API**：按教室/教师/班级查询具体课程安排的接口（可能需要单独的 API 端点）
- [ ] **sfbhkc 字段**：是否为空教室筛选参数（空=空教室，非空=有课教室？）
- [ ] **xqh_id 枚举**：其他校区（如合川校区）的 ID 值
- [ ] **xqm 枚举**：确认 `12`=春季、`3`=秋季的完整映射
- [ ] **Token 刷新机制**：webvpn-token 过期后如何自动刷新

---

## 7. 令牌更新方式

### 方式一：运行更新脚本（推荐）

```bash
# 交互式输入
python update_token.py

# 从 cURL 命令提取（最快）
python update_token.py --curl "curl 'https://...' -H 'Cookie: webvpn-token=xxx; JSESSIONID=xxx'"

# 直接传参
python update_token.py --token "eyJhbG..." --session "ABC123..."
```

### 方式二：手动编辑 .env 文件

编辑项目根目录下的 `.env` 文件：
```
QINGGUO_WEBVPN_TOKEN=你的新token值
QINGGUO_JSESSIONID=你的新session值
```

### 方式三：设置环境变量

```bash
export QINGGUO_WEBVPN_TOKEN="你的新token值"
export QINGGUO_JSESSIONID="你的新session值"
```

---

## 8. 注意事项

1. **VPN 依赖**：所有 API 请求必须通过 VPN 网关，直接访问内网 IP 无效
2. **HTTPS 证书**：VPN 代理的 HTTPS 证书可能不被信任，需要 `verify=False`
3. **请求频率**：建议请求间隔 0.5 秒以上，避免触发限流
4. **分页限制**：默认每页 15 条，可通过 `queryModel.showCount` 增大（建议不超过 500）
5. **时区**：服务器使用 Asia/Shanghai（UTC+8）
6. **编码**：请求和响应均使用 UTF-8 编码
