# classifinds
find cool stuff

#Requires some configuration files.


1. things.json (Contains items to search for)
```json
{
	"person1@gmail.com": {
		"geodes": {
			"max": 150,
			"keywords": ["beautiful", "mezmerizing"]
		},
		"motorcycle+harley": {
			"max": 6000,
			"keywords": ["motorcycle", "2015", "2016"]
		}
	},
	"person2@gmail.com": {
		"search+terms+seperated+by+plus": {
			"max": "max_price_here",
			"keywords": ["This is a list of keywords, if any of these are found in the description or title of an ad this counts as a promising ad and will be emailed to person2@gmail.com."]
		},
	}
}
```


config.ini (Contains configuration stuff)
```
[PARAMS]
zip = 12345
api_base = http://www.ksl.com/classifieds/api.php?
web_base = https://www.ksl.com/?
thumbnail = ?filter=ksl/newhl

[EMAIL]
email = youremail@gmail.com
key = email_password
```
