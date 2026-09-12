#!/bin/bash
# @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌‌​‌​‌‌​‌​​‌​‌‌​​​‌​​‌​​‌​‌​​‌‌​‌‌​​​‌​‌​‌​​​‌‌​​‌​​​‌​‌‌​​​​‌‌‌​​‌‌​‌​​​‌​‌​‌​​‌​​​​‌‌​‌​​​​‌‌​‌‌​​​​‌​‌‌​‌​‌‌​‌‌​​​‌‌‌​‌​​​‌​‌​​‌​​‌‌‌​​‌‌​‌‌​​‌​‌​‌‌​​‌​​​‌‌​‌‌​​​‌‌‌​‌‌​⁠
# Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
# Author: https://github.com/Srinivasan-78
# SPDX-License-Identifier: MIT
# Fingerprint: AMK1.MibJlTdXsEHhl-ltRsedlv

# Cairn Uninstall Script

###################################################################################################################################################################################################

# Script                | Cairn Uninstall Script
# Version               | 1.0.0
# Author                | Srinivasan Vijayaraghavan
# Website               | https://cairn.com

###################################################################################################################################################################################################
#                                                                                                                                                                                                 #
#                                                                                           Color Codes                                                                                           #
#                                                                                                                                                                                                 #
###################################################################################################################################################################################################

RESET='\033[0m'
YELLOW='\033[1;33m'
WHITE_R='\033[39m' # Same as GRAY_R for terminals with white background.
GRAY_R='\033[39m'
RED='\033[1;31m' # Light Red.
GREEN='\033[1;32m' # Light Green.

###################################################################################################################################################################################################
#                                                                                                                                                                                                 #
#                                                                                  Constants & Variables                                                                                          #
#                                                                                                                                                                                                 #
###################################################################################################################################################################################################

CAIRN_DIR="/opt/cairn"
MANAGEMENT_COMPOSE_FILE="${CAIRN_DIR}/compose.yml"

###################################################################################################################################################################################################
#                                                                                                                                                                                                 #
#                                                                                     Functions                                                                                                   #
#                                                                                                                                                                                                 #
###################################################################################################################################################################################################

header_red() {
  if [[ "${script_option_debug}" != 'true' ]]; then clear; clear; fi
  echo -e "${RED}#########################################################################${RESET}\\n"
}

check_has_sudo() {
  if sudo -n true 2>/dev/null; then
    echo -e "${GREEN}#${RESET} User has sudo permissions.\\n"
  else
    echo "User does not have sudo permissions"
    header_red
    echo -e "${RED}#${RESET} This script requires sudo permissions to run. Please run the script with sudo.\\n"
    echo -e "${RED}#${RESET} For example: sudo bash $(basename "$0")"
    exit 1
  fi
}

check_current_directory(){
  if [ "$(pwd)" == "${CAIRN_DIR}" ]; then
    echo "Please run this script from a directory other than ${CAIRN_DIR}."
    exit 1
  fi
}

ensure_management_compose_file_exists(){
  if [ ! -f "${MANAGEMENT_COMPOSE_FILE}" ]; then
    echo "Unable to find the management Docker Compose file at ${MANAGEMENT_COMPOSE_FILE}. There may be a problem with your Cairn installation."
    exit 1
  fi
}

get_uninstall_confirmation(){
  read -p "This script will remove ALL Cairn files and containers. THIS CANNOT BE UNDONE. Are you sure you want to continue? (y/n): " choice
  case "$choice" in
    y|Y )
      echo -e "User chose to continue with the uninstallation."
      ;;
    n|N )
      echo -e "User chose not to continue with the uninstallation."
      exit 0
      ;;
    * )
      echo "Invalid Response"
      echo "User chose not to continue with the uninstallation."
      exit 0
      ;;
  esac
}

ensure_docker_installed() {
    if ! command -v docker &> /dev/null; then
        echo "Unable to find Docker. There may be a problem with your Docker installation."
        exit 1
    fi
}

check_docker_compose() {
  # Check if 'docker compose' (v2 plugin) is available
  if ! docker compose version &>/dev/null; then
    echo -e "${RED}#${RESET} Docker Compose v2 is not installed or not available as a Docker plugin."
    echo -e "${YELLOW}#${RESET} This script requires 'docker compose' (v2), not 'docker-compose' (v1)."
    echo -e "${YELLOW}#${RESET} Please read the Docker documentation at https://docs.docker.com/compose/install/ for instructions on how to install Docker Compose v2."
    exit 1
  fi
}

storage_cleanup() {
  read -p "Do you want to delete the Cairn storage directory (${CAIRN_DIR})? This is best if you want to start a completely fresh install. This will PERMANENTLY DELETE all stored Cairn data and can't be undone! (y/N): " delete_dir_choice
  case "$delete_dir_choice" in
      y|Y )
          echo "Removing Cairn files..."
          if rm -rf "${CAIRN_DIR}"; then
              echo "Cairn files removed."
          else
              echo "Warning: Failed to fully remove ${CAIRN_DIR}. You may need to remove it manually."
          fi
          ;;
      * )
          echo "Skipping removal of ${CAIRN_DIR}."
          ;;
  esac
}

uninstall_cairn() {
    echo "Stopping and removing Cairn management containers..."
    docker compose -p cairn -f "${MANAGEMENT_COMPOSE_FILE}" down
    echo "Allowing some time for management containers to stop..."
    sleep 5


    # Stop and remove all containers where name starts with "cairn_"
    echo "Stopping and removing all Cairn app containers..."
    docker ps -a --filter "name=^cairn_" --format "{{.Names}}" | xargs -r docker rm -f
    echo "Allowing some time for app containers to stop..."
    sleep 5

    echo "Containers should be stopped now."

    # Remove the shared Docker network (may still exist if app containers were using it during compose down)
    echo "Removing cairn_default network if it exists..."
    docker network rm cairn_default 2>/dev/null && echo "Network removed." || echo "Network already removed or not found."

    # Remove the shared update volume
    echo "Removing cairn_cairn-update-shared volume if it exists..."
    docker volume rm cairn_cairn-update-shared 2>/dev/null && echo "Volume removed." || echo "Volume already removed or not found."

    # Prompt user for storage cleanup and handle it if so
    storage_cleanup

    echo "Cairn has been uninstalled. We hope to see you again soon!"
}

###################################################################################################################################################################################################
#                                                                                                                                                                                                 #
#                                                                                       Main                                                                                                      #
#                                                                                                                                                                                                 #
###################################################################################################################################################################################################
check_has_sudo
check_current_directory
ensure_management_compose_file_exists
ensure_docker_installed
check_docker_compose
get_uninstall_confirmation
uninstall_cairn