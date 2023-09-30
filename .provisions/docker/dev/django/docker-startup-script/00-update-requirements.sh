#!/bin/bash

FILE_FOLDER_PATH='requirements/'
SHA_DIGEST_FILE='requirements_sha256sum.lst'
DIGEST_FILE_PATH="${HOME}/"
REQUIREMENTS_FILE_PATH='requirements/development.txt'

if ! test -f "${DIGEST_FILE_PATH}${SHA_DIGEST_FILE}"; then
  echo "Digest sha256sum for ${FILE_FOLDER_PATH} do not exist, treat as first start \n"
  pip install -r ${REQUIREMENTS_FILE_PATH}
  echo "Installed pip dependecies \n"
  echo "Generating sha256sum digest for ${FILE_FOLDER_PATH}"
  echo "Generated sha256 digest, writing to file"
  find "${FILE_FOLDER_PATH}" -type f -print0 | sort -z | xargs -r0 sha256sum > "${DIGEST_FILE_PATH}${SHA_DIGEST_FILE}"
else
  echo "Digest exist checking sha256 sum"
  current_requirements_sha256sum=$(find "${FILE_FOLDER_PATH}" -type f -print0 | sort -z | xargs -r0 sha256sum)
  echo "CURRENT SHA SUM"
  echo $current_requirements_sha256sum
  echo "PATH ${DIGEST_FILE_PATH}${SHA_DIGEST_FILE}"

  if diff <(echo "$current_requirements_sha256sum") "${DIGEST_FILE_PATH}${SHA_DIGEST_FILE}" > /dev/null 2>&1
  then
    echo "No changes detect in files skip update"
  else
    echo "Detect changes in files inside folder "${DIGEST_FILE_PATH}${SHA_DIGEST_FILE}""
    echo "Running update command"
    pip install -r ${REQUIREMENTS_FILE_PATH}

    echo "Generating sha256sum digest for ${FILE_FOLDER_PATH}"
    echo "Generated sha256 digest, writing to file"
    find "${FILE_FOLDER_PATH}" -type f -print0 | sort -z | xargs -r0 sha256sum > "${DIGEST_FILE_PATH}${SHA_DIGEST_FILE}"

  fi

fi
