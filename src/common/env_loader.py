################################################################
#
# Load common imports and system envs
import sys, os, json

def load_env_for_deployment():

    # In case this is not inside docker, load all env vars from the file into the runtime:
    if os.getenv("ENV_IN_DOCKER", "0") == "0": # Set this to anything not "0" and it by pass this

        use_env         = os.getenv("ENV_DEPLOYMENT_TYPE", "Local")
        path_to_envs    = os.getenv("ENV_CL_ENV_DIR", "/opt/work/env") + "/"

        target_env_file = "dev.env"
        if use_env != "":

            # Default env file per deployment
            env_for_deploy	= {
                                "NoApps"            : {
                                                        "Name"  : "dev.env"
                                                    },
                                "JustRedis"         : {
                                                        "Name"  : "dev.env"
                                                    },
                                "JustRedisSecure"   : {
                                                        "Name"  : "secure-dev.env"
                                                    },
                                "JustDB"            : {
                                                        "Name"  : "dev.env"
                                                    },
                                "RedisLabs"         : {
                                                        "Name"  : "redis-labs.env"
                                                    },
                                "RedisLabsSecure"   : {
                                                        "Name"  : "secure-redis-labs.env"
                                                    },
                                "Local"             : {
                                                        "Name"  : "dev.env"
                                                    },
                                "LocalSecure"       : {
                                                        "Name"  : "secure-dev.env"
                                                    },
                                "Live"              : {
                                                        "Name"  : "secure-dev.env"
                                                    }
                                }

            org_paths_to_test   = [
                                    "../../../env/",
                                    "../../env/",
                                    "../env/",
                                    "./env/"
                                ]
            env_paths_to_test   = os.getenv("ENV_SUPPORTED_ENV_PATHS", org_paths_to_test)
            env_file            = path_to_envs + str(target_env_file)
            if os.path.exists(env_file) == False:
                for dir_test in env_paths_to_test:
                    env_file    = str(dir_test) + str(target_env_file)
                    if os.path.exists(env_file) == True:
                        break
            # end of loading the env inside or outside docker

            if os.path.exists(env_file):
                debug           = False

                if debug:
                    print ""
                    print "Manually assigning Environment variables from file: " + str(env_file)
                    print ""

                for raw_line in open(env_file).readlines():
                    line        = str(raw_line).replace("\n", "")
                    if "#" not in str(line) and "=" in str(line):
                        splt_ar = line.split("=")
                        if len(splt_ar) > 0:
                            key     = splt_ar[0]
                            if str(key) != "ENV_IN_DOCKER":
                                value   = "=".join(splt_ar[1:])
                                os.environ[str(key)] = value

                                if debug:
                                    print str(key) + " => " + str(value)
                        # end of if the file has 
                    # end of checking if the line has an # and = characters
                # end of for all lines in the env file to load in this is not inside docker

                if debug:
                    print ""
            else:
                print "Did not find the Environment file: " + str(env_file)
            # end of loading env in case this is not inside docker 
        else:
            print "Not have a valid deployment type:" + str(use_env)
        # end of if valid use_env != "":
    # end of loading for a command-line deployment type
# end of load_env_for_deployment

#
#
################################################################
