# MagicCMD
CMD and Powershell for nubs as me)
всегда мне было сложно запоминать правильное написание команд, да и сами команды тоже. А вот через этот инструмент (если ты здесь, то уже понимаешь) крайне функционален при определенном уровне знаний. alt+tab --> google --> ctrl+c--> alt+tab--> ctrl+v, и это при хорошем раскладе когда особо то не нужно ничего , просто нет такой кнопки! или настройки! или "управляет ваша организация"... грусть... 
ПРЕДСТАВЛЯЮ ДЕТИЩЕ века синтетического разума!  Я пока сам слабо себе представляю о спектре возможностей раскрывающихся с этим небольшим tools написанным тем же AI под моим чутким руководством, думаю нам всем предстоит еще много открытий по мере ипользования) ну в общем... Пишешь прям на русском, или на любом другом языке, что тебе нужно AI формирует логику исполнения и выполнения, возвращает тебе уже выполняемые команды! когда это заработало я пищал как малолетняя девочка) Это взаимодействие AI с вашим рабочим столом и файловой системой по средствам обычного чата только в командной строе) Экспериментируйте! безусловно это можно расширить и масштабировать на различные другие терминалы) 

батник build.bat собирает питоном .exe файл, для выполнения на любом пк, пакуя его всеми необходимыми пакетами для работы из коробки. правда не стал туда же подтягивать поддержку CUDA для gpu locale llm ибо бесплатные лимиты groq вполне меня устраивают, так же как и скорость!, поэтому регистрируйтесь, создавайте ключ, копипаст и вперед! exe если что будет весить 230 +- mb 

MagicCMD — minimal distributable

Included files:
- interpreter_bootstrap.py  (main interpreter loop, elevation)
- agent_api.py    (permissioned command execution API)
- run.py          (legacy runner)

Usage:
1) Unzip to a folder on Windows.
2) Run run.py (idk mb as Administrator)  OR make .exe pyinstaller --onefile run.py
3) On first run, enter/confirm your GROQ API key when prompted.
4) Use the assistant; it will request permission before making system changes. Use 'a' to allow "yes to all" for the session.

Note: Do NOT distribute any secret keys. This package does not embed API keys. Replace or set GROQ_API_KEY via environment or magickcfg.json.
