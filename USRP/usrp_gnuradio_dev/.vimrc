set enc=utf-8

" Show some context around the current line
set scrolloff=2

" Folds should be specified by three {'s and three }'s
set fdm=marker

" Indenting options
set tabstop=4
set shiftwidth=4
set autoindent
"set smartindent
set expandtab

" Pretty colors
syntax enable
set t_Co=256
" colorscheme wombat256

" Show unfinished commands and set more bash-like tab completion
set showcmd
set wildmode=longest,list,full
set wildmenu

" Case insensitive search-as-you-type
set incsearch
set ignorecase
set smartcase

" Mouse support
"set mouse=a

" Not helpful for php, really use this for html files?
" Match < and > in html documents
"au FileType html set mps+=<:>

if has("autocmd")
  " Enable file type detection.
  " Use the default filetype settings, so that mail gets 'tw' set to 72,
  " 'cindent' is on in C files, etc.
  " Also load indent files, to automatically do language-dependent indenting.
  filetype plugin indent on
endif
