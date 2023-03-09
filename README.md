# TCP chat

## Overview

Asynchronous TCP chat based on asyncio. TLS is used.

Client <-> server model was used. Consequently, project as such consists of two main parts: ```client.py``` and ```server.py```. There may be many clients but only one server.

## Example of usage

Once you have installed the project, you must always set environment variables for server host, server port, etc. prior to client or server invocation.
Now you can start a server and multiple clients:
<pre>
source set_environment_variables.sh
python server.py
</pre>
In another shell to create the first client:
<pre>
source set_environment_variables.sh
python client.py
</pre>
In yet another shell to create the second client:
<pre>
source set_environment_variables.sh
python client.py
</pre>

Have a great chat!

## Credentials

https://www.roguelynn.com/words/asyncio-we-did-it-wrong/ - awesome article about asyncio that sheds light on non-trivial challenges that one can encounter;<br>
https://pymotw.com/3/asyncio/io_coroutine.html - topic on pyMOTW which covers asyncio streams.
