pipeline {
    agent { label 'windows' }

    stages {

        def build_failures = false

        stage('InstallPrereqs') {
            steps {
                bat 'python -m pip install -r requirements.txt'
            }
        }

        try{
            stage('mypy verification') {
                steps {
                    bat 'python -m mypy BlenderImporters FileUtilities RainbowFileReaders UnrealImporters tests GameDataExample.py MAPConverter.py RSBPNGCacheGenerator.py RSBtoPNGConverter.py SOBtoOBJConverter.py'
                }
            }
        } catch(e) {
            build_ok = true
            echo e.toString()  
        }
        
        stage('Unit Test') {
            steps {
                bat 'python -m unittest discover'
            }
        }

        if(build_failures) {
            currentBuild.result = "FAILURE"
        } else {
            currentBuild.result = "SUCCESS"
        }
    }
}
