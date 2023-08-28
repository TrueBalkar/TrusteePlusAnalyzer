# TrusteePlusAnalyzer
## Version 0.033 alpha of the project          
Still rough around the edges and very slow, but overall it is working!                   

#### How to start scanner:
1. Open Android studio using command 'sudo android-studio';
2. Start emulator in Android Studio;
3. Afterward run bash script using command './run.sh' and click on tools tab at side to hide it;
4. Open PyCharm and run 'run.py' script. Alternatively you can run it from console, but firstly you will need to enter virtual env;
5. Select emulator screen and press F12 to enter full-screen mode (you need to do that fast);
6. Wait till scanner finishes working;

#### How to see logs:
1. Connect to machine using SSH;
2. Login;
3. Type './service.sh';

#### How to analyze two app versions:
1. Specify templates names in 'config.ini' file, for reference template and new app template paths;
2. Open PyCharm and run 'analyzer.py' script in analyzer directory. Alternatively you can run it from console, but firstly you will need to enter virtual env;

## How does scanner works?
It interacts with screen and make screenshots. Afterward those screenshots are put in queue to be processed
and to get information about text and objects from images. That information then is put in the queue to be used in navigating
through the app.

#### Technologies used:
- Keras OCR;
- Open-CV;
- PyAutoGUI;
- SciPy;
- sklearn;
- pandas;
- etc.

## How does analyzer works?
It reads information about reference app and new app, which is then used to compare that info.
Afterward it creates new directory with info about differences of two versions.

Technologies used:
- pandas;
- SciPy;
- NLTK;
- etc.

## Plans for the future:
- Creation of neural networks to manage, clean and process all the information;
- Implementation of multiple device synchronised scanning;
- Lots of fun stuff;