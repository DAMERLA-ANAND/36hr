# 📘 **JSearch API — Job Search Endpoint Documentation (`GET /search`)**

The **Job Search** endpoint returns job postings based on a flexible natural-language `query` and multiple optional filtering parameters.

Base URL:

arduino

Copy code

`https://jsearch.p.rapidapi.com/search`

---

# 🟥 **1\. Required Query Parameter**

## **`query` (string — required)**

Free-form job search text.  
It is recommended to include **job title + location**.

**Examples:**

- `developer jobs in chicago`
- `web development jobs in chicago`
- `marketing manager in new york via linkedin`

---

# 🟦 **2\. Pagination Parameters**

## **`page` (number — optional)**

Page index to return (each page contains **10 results**).  
**Default:** `1`  
**Allowed:** `1–50`

---

## **`num_pages` (number — optional)**

Total number of result pages to fetch starting from `page`.  
**Default:** `1`  
**Allowed:** `1–50`

> **Note:** Each page (10 results) consumes **one request** from quota.

---

# 🟩 **3\. Location Parameters**

## **`country` (string — optional)**

ISO-3166-1 alpha-2 country code.

**Default:** `us`  
Example:

- For Berlin jobs → `country=de`

Full list: [https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)

---

## **`radius` (number — optional)**

Return jobs within a distance (km) from the location inside the query.  
Internally uses Google “radius” parameter it might not produce exact behavior.

---

# 🟨 **4\. Language & Time Filters**

## **`language` (string — optional)**

ISO-639 language code for job postings.

If empty → primary language of the specified `country` is used.  
If unsupported → no results returned.

Values list: [https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes)

---

## **`date_posted` (enum — optional)**

Filter by job posting age.

**Default:** `all`  
**Allowed:**

- `all`
- `today`
- `3days`
- `week`
- `month`

---

# 🟪 **5\. Employment / Requirements Filters**

## **`employment_types` (string — optional)**

Comma-separated list of employment type filters.

Allowed:

- `FULLTIME`
- `CONTRACTOR`
- `PARTTIME`
- `INTERN`

**Example:**

ini

Copy code

`employment_types=FULLTIME,INTERN`

---

## **`job_requirements` (string — optional)**

Comma-separated list of experience/qualification flags.

Allowed:

- `under_3_years_experience`
- `more_than_3_years_experience`
- `no_experience`
- `no_degree`

**Example:**

ini

Copy code

`job_requirements=no_experience,no_degree`

---

# 🟫 **6\. Work-Mode Filters**

## **`work_from_home` (boolean — optional)**

Return only remote jobs.

**Default:** `false`

---

# 🟧 **7\. Publisher Filters**

## **`exclude_job_publishers` (string — optional)**

Comma-separated list of job publishers to exclude.

**Example:**

ini

Copy code

`exclude_job_publishers=BeeBee,Dice`

---

# 🟩 **8\. Response Field Selection**

## **`fields` (string — optional)**

Comma-separated list of fields to include in the response.

If omitted → **all fields** returned.

**Example:**

ini

Copy code

`fields=employer_name,job_publisher,job_title,job_country`

---

# 🧪 **Sample Python (Requests) Code**

python

Copy code

`import requests  url = "https://jsearch.p.rapidapi.com/search"  querystring = {     "query": "developer jobs in chicago",     "page": "1",     "num_pages": "1",     "country": "us",     "date_posted": "all" }  headers = {     "x-rapidapi-key": "YOUR_API_KEY",     "x-rapidapi-host": "jsearch.p.rapidapi.com" }  response = requests.get(url, headers=headers, params=querystring)  print(response.json())`

---

# 📘 JSearch API — **Job Details Endpoint Documentation**

## **Endpoint**

**GET** `https://jsearch.p.rapidapi.com/job-details`

This endpoint retrieves **detailed information for a specific job posting**, identified by its `job_id`.

---

## 🔧 **Query Parameters**

Parameter

Type

Required

Default

Description

**job_id**

string

**Yes**

—

ID of the job to fetch details for. Supports batching up to 20 IDs separated by commas.

**country**

string

Optional

`"us"`

ISO 3166-1 alpha-2 country code determining results region.

**language**

string

Optional

—

ISO 639 language code specifying the language of the returned job details. Defaults to primary language of chosen country.

**fields**

string

Optional

—

Comma-separated list of fields to include in the response (field projection). If omitted, all fields are returned.

### Example values from the screenshot:

- `job_id: "gcnkkB1_QjIlxbV9AAAAAA=="`
- `country: "us"`

---

## 🔑 **Required Headers**

Header

Value

`x-rapidapi-key`

Your RapidAPI key (e.g., `d10b99d95emsh41c...`)

`x-rapidapi-host`

`jsearch.p.rapidapi.com`

---

## 📥 **Request Example (Python – Requests)**

python

Copy code

`import requests  url = "https://jsearch.p.rapidapi.com/job-details"  querystring = {     "job_id": "gcnkkB1_QjIlxbV9AAAAAA==",     "country": "us" }  headers = {     "x-rapidapi-key": "YOUR_API_KEY",     "x-rapidapi-host": "jsearch.p.rapidapi.com" }  response = requests.get(url, headers=headers, params=querystring)  print(response.json())`

---

## 📤 **Response**

`
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string"
    },
    "request_id": {
      "type": "string"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "job_id": {
          "type": "string"
        },
        "country": {
          "type": "string"
        },
        "language": {
          "type": "string"
        }
      }
    },
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "job_id": {
            "type": "string"
          },
          "job_title": {
            "type": "string"
          },
          "employer_name": {
            "type": "string"
          },
          "employer_logo": {
            "type": "null"
          },
          "employer_website": {
            "type": "null"
          },
          "job_publisher": {
            "type": "string"
          },
          "job_employment_type": {
            "type": "string"
          },
          "job_employment_types": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "job_apply_link": {
            "type": "string"
          },
          "job_apply_is_direct": {
            "type": "boolean"
          },
          "apply_options": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "publisher": {
                  "type": "string"
                },
                "apply_link": {
                  "type": "string"
                },
                "is_direct": {
                  "type": "boolean"
                }
              }
            }
          },
          "job_description": {
            "type": "string"
          },
          "job_is_remote": {
            "type": "null"
          },
          "job_posted_at": {
            "type": "string"
          },
          "job_posted_at_timestamp": {
            "type": "integer"
          },
          "job_posted_at_datetime_utc": {
            "type": "string"
          },
          "job_location": {
            "type": "string"
          },
          "job_city": {
            "type": "string"
          },
          "job_state": {
            "type": "string"
          },
          "job_country": {
            "type": "string"
          },
          "job_latitude": {
            "type": "number"
          },
          "job_longitude": {
            "type": "number"
          },
          "job_benefits": {
            "type": "null"
          },
          "job_google_link": {
            "type": "string"
          },
          "job_salary": {
            "type": "null"
          },
          "job_min_salary": {
            "type": "null"
          },
          "job_max_salary": {
            "type": "null"
          },
          "job_salary_period": {
            "type": "null"
          },
          "job_highlights": {
            "type": "object",
            "properties": {
              "Qualifications": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              },
              "Responsibilities": {
                "type": "array",
                "items": {
                  "type": "string"
                }
              }
            }
          },
          "job_onet_soc": {
            "type": "string"
          },
          "job_onet_job_zone": {
            "type": "string"
          }
        }
      }
    }
  }
}

`
