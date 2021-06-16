# CLscraper

A simple Python script that will send you emails when a craigslist search query gets new results.


## Install 

python must already be installed.

```bash
git clone https://github.com/hugolarde/CLscraper
cd CLscraper
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

Additionally, to use Gmail servers, You must set up your gmail account to work with "less secure apps" [here](https://myaccount.google.com/lesssecureapps?pli=1). 
You can also make a new gmail account to do this if your main one has two factor authentification or you generally want stronger security.

## Configure
Create a `config.ini` file and configure all the parameters. A description for each parameter is provided in the file `example_file.ini` wich can be used as a base for your custom configuration. 

## Run
To start the program: 
```bash
python CLscraper.py config.ini
```
And to keep the program running after closing the terminal: 
```bash
 nohup python CLscraper.py config.ini &
 ```
