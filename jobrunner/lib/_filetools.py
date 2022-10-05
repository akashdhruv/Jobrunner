# Standard libraries
import os
import subprocess

import toml


def ParseJobToml(basedir, workdir):
    """
    `basedir` : base directory
    `workdir` : work directory
    """
    # Build a list of all toml files in the directory structure
    jobtoml_list = GetFileList(basedir, workdir, "job.toml")

    # Create an empty dictionary for job object
    main_dict = {
        "job": {
            "schedular": "None",
            "input": "None",
        },
        "config": {
            "commands": [],
            "schedular": [],
            "source": [],
            "scripts": [],
            "setup": [],
        },
    }

    # Loop over individual files
    for jobtoml in jobtoml_list:

        # Load the toml file
        job_dict = toml.load(jobtoml)

        # parse `job` in job_dict
        # and update main_dict
        if "job" in job_dict:

            # looping over items
            for key, value in job_dict["job"].items():
                main_dict["job"].update({key: value})

        # parse job config and loop
        # over items
        if "config" in job_dict:

            # looping over items
            for key, value_list in job_dict["config"].items():

                # special case for `source` and `scripts` assign
                # absolute path
                if key in ["source", "scripts", "setup"] and value_list:
                    value_list = [
                        jobtoml.replace("job.toml", value) for value in value_list
                    ]

                # extend main dict
                main_dict["config"][key].extend(value_list)

    # Add basedir and workdir to main_dict
    # for future use
    main_dict["basedir"] = basedir
    main_dict["workdir"] = workdir

    return main_dict


def RunConfigScripts(main_dict):
    """
    run scripts

    `main_dict` : job dictionary
    """
    for script in main_dict["config"]["scripts"]:
        subprocess.run(f"{script}", shell=True, check=True)


def RunSetupScripts(basedir, setup_list):
    """
    run setup scripts

    `basedir`  : base directory
    `setup_list` : list of setup scripts
    """
    for script in setup_list:
        os.chdir(os.path.dirname(script))
        subprocess.run(f"{script}", shell=True, check=True)

    os.chdir(basedir)


def CreateInputFile(main_dict):
    """
    create an input file for a given simulation recursively using
    `job.input` between `basedir` and `workdir`

    `main_dict` : job dictionary
    """
    # get inputfile_list from internal method
    inputfile_list = GetFileList(
        main_dict["basedir"], main_dict["workdir"], "job.input"
    )

    # run a subprocess to build flash.par
    process = subprocess.run(
        f'rm -f {main_dict["job"]["input"]} && cat {" ".join(inputfile_list)} > {main_dict["job"]["input"]}',
        shell=True,
        check=True,
    )


def CreateJobFile(main_dict):
    """
    create `job.sh` for a given simulation recursively using configuration
    `job` dictionary

    `main_dict`       :  Job dictionary
    """
    # set header for the submit script
    with open(main_dict["workdir"] + "/" + "job.sh", "w") as jobfile:

        # write the header
        jobfile.write("#!/bin/bash\n\n")

        # Add schedular commands
        for entry in main_dict["config"]["schedular"]:
            jobfile.write(f"{entry}\n")

        # Add an extra space
        jobfile.write("\n")

        # Add commands to source scripts
        for entry in main_dict["config"]["source"]:
            jobfile.write(f"source {entry}\n")

        # Add an extra space
        jobfile.write("\n")

        # Add bash commands
        for entry in main_dict["config"]["commands"]:
            jobfile.write(f"{entry}\n")


def GetFileList(basedir, workdir, filename):
    """
    Get a list of paths containing a file with name
    `filename` between `basedir` and `workdir`

    Arguments
    ---------
    `basedir`  :  Base directory (top level) of a project
    `workdir`  :  Current job directory
    `filename` :  Name of the file to query

    Returns
    --------
    file_list :   A list of path containing the file
    """

    # Get a list of directory levels between `basedir` and `workdir`
    dir_levels = [
        "/" + level for level in workdir.split("/") if level not in basedir.split("/")
    ]

    # Create an empty file list
    file_list = []

    # start with current level
    current_level = basedir

    # Loop over directory levels
    for level in [""] + dir_levels:

        # Set current level
        current_level = current_level + level

        # set file path
        file_path = current_level + "/" + filename

        # Append to file list if path exists
        if os.path.exists(file_path):
            file_list.append(file_path)

    return file_list
