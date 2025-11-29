rm -rf package
mkdir package
cp dist/lucky-lillia-desktop.exe package/lucky-lillia-desktop.exe
cp package.json package/
tar -czf luck-lilia-desktop-win-x64.tgz package/*
npm publish luck-lilia-desktop-win-x64.tgz