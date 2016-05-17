# classifinds
find cool stuff

Required files:

## 1. things.json (Contains items to search for)
```json
{	
	"bob": {
		"email": "youremail@gmail.com",
		"phone": "123456789",
		"carrier": "verizon",
		"things": {
			"http://www.ksl.com/?nid=231&nocache=1&search=geodes&zip=&distance=&min_price=&max_price=&type=&x=0&y=0": {
				"text": true,
				"keywords": ["beautiful", "mezmerizing"]
			}
		}
	}
}
```

## 2. config.ini (Contains configuration stuff)
```
[PARAMS]
api_base = http://www.ksl.com/classifieds/api.php?
web_base = https://www.ksl.com/?
thumbnail = ?filter=ksl/newhl

[EMAIL]
email = youremail@gmail.com
key = email_password
```
