```sh
mkdir -p ~/.local/bin

ln -sf /Users/matthuang/Desktop/dev/open/toolbox/bin/tbx ~/.local/bin/tbx

echo $PATH
```


`@~/.zshrc`
```sh
# add
export PATH="$HOME/.local/bin:$PATH"
```

--- rm
```sh
rm ~/.local/bin/tbx
```
