pipeline {
    agent { label 'windows' }

    stages {
        stage('InstallPrereqs') {
            steps {
                bat 'python -m pip install -r requirements.txt'
            }
        }
        stage('Parallel tests') {
            failFast false
            parallel {
                stage('mypy verification') {
                    steps {
                        bat 'python -m mypy BlenderImporters FileUtilities RainbowFileReaders UnrealImporters tests GameDataExample.py MAPConverter.py RSBPNGCacheGenerator.py RSBtoPNGConverter.py SOBtoOBJConverter.py'
                    }
                }
                stage('Unit Test') {
                    steps {
                        bat 'python -m unittest discover'
                    }
                }
            }
        }
    }
}
