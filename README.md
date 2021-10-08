# keyword-price-api




| method | url                                                  | input format | output format | desc                                                                               |
| :----: | ---------------------------------------------------- | ------------ | :-----------: | ---------------------------------------------------------------------------------- |
|  GET   | [/api/v1/results/keyword](#get-get-keywords)         | n/a          |     JSON      | 각 카테고리별 키워드들의 출현빈도와 출현된 productId 리스트를 리턴                 |
|  GET   | [/api/v1/results/price-spread](#get-get-pricespread) | n/a          |     JSON      | 각 카테고리 아이템들의 가격분포를 histogram으로 나타낸 이미지 링크들을 dict로 리턴 |
|  POST  | [/api/v1/feedback](#post-read-feedback)              | JSON         |      str      | 유저의 피드백을 읽어들여 다음 get메소드들이 호출될때 반영되게 함                   |


# **Code Workflow**



# **API calls**


## [`GET`] get-keywords

URL: `/api/v1/results/keyword`

  각 카테고리별 키워드들의 출현빈도와 출현된 productId 리스트를 리턴

### **Responses**


**Successful Response**
  * **Code:** 200 <br />
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


**Sample Call:**

```
curl --location --request GET 'http://175.106.99.99:16758/api/v1/results/price-spread'
```


## [`GET`] get-pricespread
----
URL: `/api/v1/results/price-spread`

  각 카테고리 아이템들의 가격분포를 histogram으로 나타낸 이미지 링크들을 dict로 리턴l,

### **Responses**

**Successful Response**
  * **Code:** 200 <br />
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
  * **Code:** 200 <br />
    **Content:** `"received feedback"`

### **Sample Call:**

```
curl --location --request POST 'http://175.106.99.99:16758/api/v1/feedback' \
--data-raw '[
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
        "sub-cats": [],
        "ignore": [],
        "effective": []
    }
]'
```

