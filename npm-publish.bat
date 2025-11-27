mv dist package
cp package.json package/
tar -czf luck-lilia-desktop-win-x64.tgz package/*
npm publish luck-lilia-desktop-win-x64.tgz