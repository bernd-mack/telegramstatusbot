# telegramstatusbot
### Description
This code is designed to create a telegram message every day with a masternodeoverview of the current running and minting masternodes and some daily statistics. For this purpose some masternodepool APIs are collected and merged together with a current list of masternodes of the defichain and then compared to the state of the masternodes 24h ago. Every run of the code stores the current state to the local memory. 

### Example telegram message
<code>Count masternodes</code><br>
<code>24h blocks (mean searchtime)</code><br>
<code>------------------</code><br>
<code>total     8319</code><br>
<code>7688 ( 1.1 days)</code><br>
<code>------------------</code><br>
<code>cakedefi  7350</code><br>
<code>6829 ( 1.1 days)</code><br>
<code>community  846</code><br>
<code> 742 ( 1.1 days)</code><br>
<code>mydeficha  120</code><br>
<code> 117 ( 1.0 days)</code><br>
<code>Nodehub      3</code><br>
<code> n/a ( inf days)</code><br>
<code>------------------ </code><br>

### Installation
1. Install python3.9<code>sudo apt-get install python3.9</code>
2. Download the sourcecode to your working directory <code>wget https://github.com/bernd-mack/telegramstatusbot/archive/refs/tags/0.1.tar.gz</code>
3. Install the required modules for python requirements.txt <code>pip install -r requirements.txt</code>
4. Set up your telegram Bot with @BotFather https://core.telegram.org/bots
5. Edit the credentials.py with your Bot Token and ChatID 
6. Set up cronjob (crontab -e) to run the python code every 24h 5min until midnight<br>
<code>55 23 * * * /usr/local/bin/python3.9 /home/username/statusbot.py</code>

### Contact
www.mydeficha.in <br />
https://t.me/mydefichain