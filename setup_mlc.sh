#!/bin/bash

# # Displays information on how to use script
# helpFunction()
# {
#   echo "Usage: $0 [-d small|all]"
#   echo -e "\t-d small|all - Specify whether to download entire dataset (all) or just 1000 (small)"
#   exit 1 # Exit script after printing help
# }

# # Get values of command line flags
# while getopts d: flag
# do
#   case "${flag}" in
#     d) data=${OPTARG};;
#   esac
# done

# if [ -z "$data" ]; then
#   echo "[ERROR]: Missing -d flag"
#   helpFunction
# fi

# Install Python Dependencies
echo "deb [trusted=yes] http://apt-proxy.tcsbank.ru/repository/apt-ubuntu/ focal main restricted universe multiverse" > /etc/apt/sources.list \
    && echo "deb [trusted=yes] http://apt-proxy.tcsbank.ru/repository/apt-ubuntu/ focal-updates main restricted universe multiverse" >> /etc/apt/sources.list \
    && echo "deb [trusted=yes] http://apt-proxy.tcsbank.ru/repository/apt-ubuntu/ focal-backports main restricted universe multiverse" >> /etc/apt/sources.list \
    && echo "deb [trusted=yes] http://apt-proxy.tcsbank.ru/repository/apt-ubuntu/ focal-security main restricted universe multiverse" >> /etc/apt/sources.list 

apt update && apt install -y openjdk-21-jdk

pip3 uninstall -y lmms-eval
conda install -y spacy

# Install Environment Dependencies via `conda`
conda install -y -c pytorch faiss-cpu;
conda install -y -c conda-forge openjdk=21;

pip install -r requirements_updated.txt;
cp /workspace/RL4VLM/VLM_PPO_miniworld/prepared_data/items_ins_v2.json /workspace/RL4VLM/VLM_PPO_miniworld/prepared_data/items_shuffle.json /workspace/RL4VLM/VLM_PPO_miniworld/WebShop/data/

# Download dataset into `data` folder via `gdown` command
# mkdir -p data;
# cp -r SOURCE_DATA_FOLDER/* data/
# Download spaCy large NLP model
python -m spacy download en_core_web_sm

# Build search engine index
cd search_engine
mkdir -p resources resources_100 resources_1k resources_100k
python convert_product_file_format.py # convert items.json => required doc format
mkdir -p indexes
./run_indexing.sh
cd ..

# Create logging folder + samples of log data
# get_human_trajs () {
#   PYCMD=$(cat <<EOF
# import gdown
# url="https://drive.google.com/drive/u/1/folders/16H7LZe2otq4qGnKw_Ic1dkt-o3U9Zsto"
# gdown.download_folder(url, quiet=True, remaining_ok=True)
# EOF
#   )
#   python -c "$PYCMD"
# }
# mkdir -p user_session_logs/
# cd user_session_logs/
# echo "Downloading 50 example human trajectories..."
# get_human_trajs
# echo "Downloading example trajectories complete"
# cd ..