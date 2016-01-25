#WOS

##Install

```
git clone wostext
cd wostext
pip install -r requirements.pip

```

##Use WOS
Full code source is inside wos.py

WOS has to been called at the end of the file such as :


```
    code: python
    if __name__=="__main__":
        WOS(
            query='TS=(complexity OR "complex system*")', 
            outfile="complexity", username="myusername", 
            password="mypassword")
```
* query 
    a query previously checked in WOS accepts every parameters that follow the WOS syntax
    specified in [advanced search example] (https://images-webofknowledge-com.fennec.u-pem.fr/WOKRS521R5/help/WOS/hp_advanced_examples.html)
* outfile
    give a name to your result file without the extension the program will write a file for every 500 results
* username
    specific username from your UPEM account
* password
    specific username from your UPEM account

** A private.py file with username and password is loaded in case you didn't provide your account
see [private.py](../blob/master/private.py) 



