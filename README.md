# keyword-price-api

- [keyword-price-api](#keyword-price-api)
- [**Typical Workflow**](#typical-workflow)
- [**API calls**](#api-calls)
  - [[`GET`] get-keywords](#get-get-keywords)
    - [**Responses**](#responses)
    - [**Sample Call:**](#sample-call)
    - [**Code Workflow**](#code-workflow)
  - [[`GET`] get-pricespread](#get-get-pricespread)
    - [**Responses**](#responses-1)
    - [**Sample Call:**](#sample-call-1)
    - [**Code Workflow**](#code-workflow-1)
  - [[`POST`] read-feedback](#post-read-feedback)
    - [**Input Data Params**](#input-data-params)
    - [**Responses**](#responses-2)
    - [**Sample Call:**](#sample-call-2)
    - [**Important Note**](#important-note)
    - [**Code Workflow**](#code-workflow-2)

**Base Path**: `http://175.106.99.99:16758/`



| method | url                                                  | input format | output format | desc                                                                               |
| :----: | ---------------------------------------------------- | ------------ | :-----------: | ---------------------------------------------------------------------------------- |
|  GET   | [/api/v1/results/keyword](#get-get-keywords)         | n/a          |     JSON      | 각 카테고리별 키워드들의 출현빈도와 출현된 productId 리스트를 리턴                 |
|  GET   | [/api/v1/results/price-spread](#get-get-pricespread) | n/a          |     JSON      | 각 카테고리 아이템들의 가격분포를 histogram으로 나타낸 이미지 링크들을 dict로 리턴 |
|  POST  | [/api/v1/feedback](#post-read-feedback)              | JSON         |      str      | 유저의 피드백을 읽어들여 다음 get메소드들이 호출될때 반영되게 함                   |


# **Typical Workflow**

beforehand: MongoDB에 타겟 데이터베이스 업로드

**for** *i = 1* **to** *repeat* **do**:

{
   1. [GET-KEYWORDS](#get-get-keywords)

      a. i=1: 최초 상태에서 각 카테고리별 키워드 정보 반환

      b. i>=2: 피드백이 반영된 키워드 정보와 #3을 위한 가장최근 피드백 반환
   2. [GET-PRICESPREAD](#get-get-pricespread):  (optional)

      a. i=1: 각 카테고리 아이템들의 가격분포를 histogram으로 나타낸 이미지 링크들을 dict로 리턴
      
      b. i>=2: 피드백 입력 후: 피드백이 반영된 histogram링크 반환
   3. [POST-FEEDBACK](#post-read-feedback)
   
      a. i=1: #2, #3의 정보를 기반으로 tweak하고 싶은 부분을 피드백으로 입력

      b. i>=2: #1의 가장 최근 피드백을 ***기반***으로 새로운 옵션을 ***추가***하여 입력
      
      *Note*: [**Important Note**](#important-note) 참조



}

**END IF:** retrieved satisfactory information

# **API calls**


## [`GET`] get-keywords

URL: `/api/v1/results/keyword`

  각 카테고리별 키워드들의 출현빈도와 출현된 productId 리스트를 리턴

### **Responses**


**Successful Response**

**Code:** 200 <br />
**Content:**
    
- **result**: array of category-objs
    - **category-objects**
        | attributes | type                    | desc      | uses |
        | ---------- | ----------------------- | --------- | ---- |
        | categ      | str                     |           |      |
        | keywords   | list of keyword-objects | 아래 참조 |      |  |

      

    - **keyword-objects**
      | attributes   | type         | desc                                   | uses                                                |
      | ------------ | ------------ | -------------------------------------- | --------------------------------------------------- |
      | rank         | int          | 출현 빈도별 순위                       |                                                     |
      | keyword      | str          | 키워드 이름                            |                                                     |
      | appearance   | int          | 출현빈도                               | *note: 출현빈도와 product_list의 값이 다를 수 있음* |
      | product_list | list of ints | 키워드가 등장하는 아이템들의 productId |                                                     |
      
- **previous-feedback**: 이전에 POST됬던 피드백 json; 자료구조는 [read-feedback](#post-read-feedback) 참조

*예시*

    ```
    {
        "result": [
            {
                "categ": "휴대용선풍기",
                "keywords": [
                    {
                        "rank": 1,
                        "keyword": "선풍기",
                        "appearance": 5,
                        "product_list": [
                            "82497194884"
                        ]
                    },
                    {
                        "rank": 2,
                        "keyword": "클립",
                        "appearance": 1,
                        "product_list": [ 
                            "82497194884"
                        ]
                    },
            },
            {
                "categ": "먼지차단마스크",
                "keywords": [
                    {
                        "rank": 1,
                        "keyword": "마스크",
                        "appearance": 32,
                        "product_list": [
                            "27224642701",
                            "26883864380",
                            "25295068476",
                        ]
                    },
                ]
            }
        "previous-feedback": [
            {
                "categ": "골프백세트",
                "lprice": 60000,
                "hprice": 150000,
                "sub-cats": [
                    "골프파우치",
                    "보스턴백"
                ],
                "ignore": [
                    "골프b",
                    "b카카오프렌즈",
                    "럭키",
                    "베이직"
                ],
                "effective": [
                    "공식몰",
                    "정품급",
                    "PLACEHOLDER"
                ]
            }
        ]
    }        
    ```


### **Sample Call:**

```
curl --location --request GET 'http://175.106.99.99:16758/api/v1/results/price-spread'
```
### **Code Workflow**

1. Dataset Prep & Cleaning
   1. target DB를 mongoDB로부터 읽어와 아래와 같은 DataFrame obj를 생성함
![dataprice](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/8314sdgsd0sk2omn6an0.png)
   2. `current_cat`는 현재 아이템의 최하위 카테고리를 가르키는 포인터 역할을 함
   3. `title` 열은 각종 특수문자를 제거하여 다시 저장됨
    ```
    i.e. 
    (칼렛바이오)(NEXT-M)<b>카카오프렌즈 골프</b> 마스크 세탁 30회 다회용마스크 (6395452)
                                    ⬇️
    칼렛바이오 NEXT-M 카카오프렌즈 골프 마스크 세탁 30회 다회용마스크
    ```
   4. 피드백의 `sub-cats`가 제공되었을 경우 하위 카테고리를 그 카테고리에 합침
    ```
    i.e. 
    "categ": "골프백세트",
    "sub-cats": [
        "골프파우치",
        "보스턴백"
    ],
    ```
    이 경우,
    ```
    골프백세트 + 보스턴백 + 골프파우치 => 골프백세트로 합쳐짐
    `current_cat`열의 값이 모두 골프백세트로 변경됨
    ```

1. Keyword Extraction 1 [피드백이 제공지 않은 경우]
   1. 각 카테고리의 아이템들에서 출현한 모든 키워드들을 `dict{Category: Counter(keywords)}`로 저장
   
      a. i.e. {`Category1` : `[('백인',23), ('이너백',12), ('핸드백',5)]`}
   

2. Keyword Extraction 2 [피드백이 제공된 경우]
   1. 각 카테고리의 아이템들에서 출현한 모든 키워드들을 iterate함
   
      a. 가격이 [`lprice`, `hprice`] 안에 해당되는 경우 `gen_countobj`에 키워드 저장

      b. 가격이 이 밖에 해당되는 경우 `sus_countobj`에 키워드 저장

   2. 저장된 `Counter` 오브젝트에서 피드백이 제공된 경우 이를 반영함
   
      a. `sus_countobj`에서 `gen_countobj`의 키워드들을 제거함

      b. 남은 키워드들은 다시 한번 iterate하며 피드백의 `ignore`, `effective`항목들을 반영한다.

3. JSON Generation
- #2에서 생성된 `dict`에 기반하여 dump가능한 final JSON파일을 생성함:
    ```
    Category A
        {
            "rank": (int),
            "keyword": (str),
            "appearance": (int),
            "product_list": list(int)
        }
    ```

## [`GET`] get-pricespread
----
URL: `/api/v1/results/price-spread`

  각 카테고리 아이템들의 가격분포를 histogram으로 나타낸 이미지 링크들을 dict로 리턴

### **Responses**

**Successful Response**

**Code:** 200 <br />
**Content:**

| KEY            | VALUE             |
| -------------- | ----------------- |
| 카테고리 (str) | 이미지 링크 (str) |

예시

```
{
    "휴대용선풍기": "https://fkz-web-images.cdn.ntruss.com/price-spread/휴대용선풍기.png",
    "마스크": "https://fkz-web-images.cdn.ntruss.com/price-spread/마스크.png",
    "노트": "https://fkz-web-images.cdn.ntruss.com/price-spread/노트.png",
    "샤워가운": "https://fkz-web-images.cdn.ntruss.com/price-spread/샤워가운.png",
    "여행용세트": "https://fkz-web-images.cdn.ntruss.com/price-spread/여행용세트.png",
    "수동우산": "https://fkz-web-images.cdn.ntruss.com/price-spread/수동우산.png",
    "자동우산": "https://fkz-web-images.cdn.ntruss.com/price-spread/자동우산.png"
}
```



### **Sample Call:**

```
curl --location --request GET 'http://175.106.99.99:16758/api/v1/results/price-spread'
```

### **Code Workflow**

*for categ in all_categories_as_list:*
- DB에서 최하위카테고리==categ인 항목들을 모아 새로운 DataFrame을 생성함
- 새로 생성된 DataFrame에서 price column정보에 기반하여 seaborn.histplot(히스토그램) 생성
- boto3을 이용해 생성된 히스토그램을 objective storage에 업로드
- 업로드된 이미지 링크를 **dict**{categ: img_link} 형태로 저장
  
*end for*

*return dict*

## [`POST`] read-feedback
----
URL: `/api/v1/feedback`

  유저의 피드백을 읽어들여 다음 get메소드들이 호출될때 반영되게 함



### **Input Data Params**

- array of:
    - keyword-feedback object
    - 
        | attributes | type          | desc                                        | uses                                                                     |
        | ---------- | ------------- | ------------------------------------------- | ------------------------------------------------------------------------ |
        | categ      | str           | 키워드 이름                                 |                                                                          |
        | lprice     | int           | 정품 가격 범위의 최소 가격                  | 정품 가격범위에 속한 아이템 키워드들은 최종 반환되는 키워드들에서 제거됨 |
        | hprice     | int           | 정품 가격 범위의 최대 가격                  | "                                                                        |
        | sub-cats   | listOfStrings | 현재 카테고리에 합쳐질 하위 카테고리 이름들 | 하위 카테고리에 속한 아이템들은 모두 현재 키워드 아래로 소속됨           |
        | ignore     | listOfStrings | 무시할 키워드들                             | 최종 반환결과에서 제외됨                                                 |
        | effective  | listOfStrings | 간직할 키워드들                             | 출현빈도가 0이라도 최종 반환됨                                           |

*예시*

```
[
    {
        "categ": "골프백세트",
        "lprice": 60000,
        "hprice": 150000,
        "sub-cats": [
            "골프파우치",
            "보스턴백"
        ],
        "ignore": [
            "골프b",
            "b카카오프렌즈",
            "럭키",
            "베이직"
        ],
        "effective": [
            "공식몰",
            "정품급",
            "PLACEHOLDER"
        ]
    },
    {
        "categ": "모자",
        "lprice": 35000,
        "hprice": 55000,
        "sub-cats": [],    # they can be left as empty list
        "ignore": [],
        "effective": []
    }
]
```


### **Responses**

**Successful Response**

**Code:** 200 <br />
**Content:** `received feedback`

### **Sample Call:**

```
curl --location --request POST 'http://175.106.99.99:16758/api/v1/feedback' \
--data-raw '[
    {
        "categ": "모자",
        "lprice": 35000,
        "hprice": 55000,
        "sub-cats": [],
        "ignore": [],
        "effective": []
    },
]'
```

### **Important Note**

[**Typical Code Workflow**](#typical-code-workflow)에서 언급된 반복문에서 2번째
 iteration이상부터는 [[`GET`] get-keywords](#get-get-keywords)에서 리턴된
 `previous-feedback`값에 추가하고 싶은 피드백 옵션을 덧붙여야 합니다.

따라서 새로운 피드백을 작성할때에는 `previous-feedback`을 복사한 내용을 수정하여 POST하는 것을 권고드립니다.

i.e.
```
"previous-feedback": 
[
    {
        "categ": "골프백세트",
        "lprice": 60000,
        "hprice": 150000,
        "sub-cats": [
            "골프파우치",
            "보스턴백"
        ],
        "ignore": [
            "골프b",
            "b카카오프렌즈",
            "럭키",
            "베이직"
        ],
        "effective": [
            "공식몰",
            "정품급",
        ]
    }
]
```
새로 update된 feedback.json
```
[
    {
        "categ": "골프백세트",
        "lprice": 60000,
        "hprice": 150000,
        "sub-cats": [],             # editted
        "ignore": [
            "골프b",
            "b카카오프렌즈",
            "럭키",
            "베이직",
            "할인가",                 # added
            "golf"                  # added
        ],
        "effective": [
            "공식몰",
            "정품급",
            "해외직구",               # added
            "S급"                   # added
        ]
    }
]
```
- "sub-cats": 이미 전 iteration에서 하위 카테고리들이 합체되었으므로 옵션 제거
- "ignore": '할인가'와 'golf' 추가
- "effective": "해외직구"와 "S급" 추가

### **Code Workflow**
```
- POST된 json 파일을 읽어드림
- 추후 다른 route에서 접근가능하도록 `./cache/feedback.json` & `./cache/feedback.pkl`파일로 저장
```