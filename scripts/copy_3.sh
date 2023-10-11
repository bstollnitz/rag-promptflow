target_folder=../odsc
cp -r src/frontend $target_folder/src
cp -r chainlit.md $target_folder/chainlit.md
mkdir -p $target_folder/scripts
cp scripts/frontend.sh $target_folder/scripts/frontend.sh