$env:PATH = $env:PATH + ";C:\Program Files\Git\bin"
bash -lc "cd 'C:\Users\tchu\PycharmProjects\ad_helper' && bash .agents/ralph/loop.sh build 1" 2>&1