rm -rf package
mkdir package
cp dist/lucky-lillia-desktop.exe package/lucky-lillia-desktop.exe
cp package.json package/
tar -czf lucky-lillia-desktop-win-x64.tgz package/*
npm publish lucky-lillia-desktop-win-x64.tgz