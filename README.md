# Concurrent chat

## Overview

Concurrent chat based on asyncio.

Client <-> server model was used. Consequently, project as such consists of two main parts: ```client.py``` and ```server.py```. There may be many clients but only one server.

## Example of usage

Once you have installed the project, you can start a server and create a client:
<pre>
python -m concurrent_chat.server
</pre>
In another terminal to create the first client:
<pre>
python -m concurrent_chat.client
</pre>
In yet another terminal to create the second client:
<pre>
python -m concurrent_chat.client
</pre>

Now type something so everyone can see!

## Credentials

https://www.roguelynn.com/words/asyncio-we-did-it-wrong/ - awesome article about asyncio that sheds light on non-trivial challenges that one can encounter;<br>
https://pymotw.com/3/asyncio/io_coroutine.html - topic on pyMOTW which covers asyncio streams.
