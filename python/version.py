import logging
import pathlib

def getRevision():
    try:
        import git
    except ImportError:
        logging.warn('failed to import git')
        git = None

    if git is None:
        import subprocess

        try:
            gitRoot = str(pathlib.Path(__file__).parent)
            logging.warn('running git describe on %s', gitRoot)
            ret = subprocess.run(['git', 'describe', '--dirty'],
                                 cwd=gitRoot,
                                 stdout=subprocess.PIPE)
        except Exception as e:
            logging.warn('failed to run git describe: %s', e)
            return "unknown"

        vers = ret.stdout.strip()
        return vers.decode('latin-1')
        
    try:
        repo = git.Repo(__file__, search_parent_directories=True)
        vers = repo.git.describe(dirty=True)
        return vers
    except Exception as e:
        logging.warn('failed to fetch revision: %s', e)
        return "unknown"
    
