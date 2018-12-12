# Hexgon-Texture-Packer

1. What this does:  
    a. It packing 2D sprites into one texture. similiar tool woudl be [TexturePacker](https://www.codeandweb.com/texturepacker)  
    b. Most texture packing tool using 4 point to pack sprites, however it can wast many empty spaces.  

        These empty spaces can cause three problems:   
            1. larger final texture file size.
            2. larger memory footprint when loading into GPU.
            3. empty space wast GPU fillrate.
    c. This tool cut images using 8 points instead of 4 points (just like octagon instead of rectangle).