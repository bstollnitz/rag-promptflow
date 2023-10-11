target_folder=../odsc
rm -rf $target_folder/src/rag_flow/*
cp -r src/rag_flow/* $target_folder/src/rag_flow
cp -r src/rag_flow/.promptflow $target_folder/src/rag_flow