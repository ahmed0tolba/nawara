def getSaveImagesRepresentingTask(prompt,n_predictions,tokenizer,model,clip,processor):
    # -*- coding: utf-8 -*-
    """VIZ_T.S.Eliot

    Automatically generated by Colaboratory.

    Original file is located at
        https://colab.research.google.com/drive/1rypmmuPn7-embbJ2GKHZGvWbEbn9ZxsI

    ## **For Purposes of Documentation, this Colab book is produced by (ref [link text](https://wandb.ai/dalle-mini/dalle-mini/reports/DALL-E-mini--Vmlldzo4NjIxODA))**

    # **Our purpose as researchers in the field in digital humanities (Literary Studies) is use Open-AI DALL-E mini model (as presented in ref) to generate images from the poem "The Waste Land" which is reported to be heavily influenced by Surrealism (a 2th C. artistic movement). **

    ## Install dependencies
    """

    # never mind the next 4 commented lines, create new enviroment, install requirements from generated requirements.txt that was generated from colab site by adding the code 
    # pip freeze > requirements.txt
    # example1 = "requirements.txt"
    # file1 = open(example1, "r")
    # FileContent = file1.read()
    # print(FileContent)

    # create enviroment && activate
    # python -m venv env1
    # apt-get install python3-venv
    # python3 -m venv env1ubuntu
    # .\env1\Scripts\activate.bat 
    # source env2ubuntu/bin/activate
    # pip install -r requirements.txt
    # pip install -r requirementsubuntu.txt
    # env1\Scripts\activate
    #  Set-ExecutionPolicy RemoteSigned


    # pip install --upgrade pip # ModuleNotFoundError: No module named 'versioneer' (never mind)

    # !pip install -q transformers flax # (remove q) (never mind)
    # !pip install -q git+https://github.com/patil-suraj/vqgan-jax.git  # VQGAN model in JAX # (remove q) (never mind)
    # !pip install -q git+https://github.com/borisdayma/dalle-mini.git  # Model files # (remove q) (never mind)
    # pip install Pillow
    """## Generate encoded images

    We generate prediction samples from a text prompt using `flax-community/dalle-mini` model.
    """
    print("hi-2")
    from dalle_mini.model import CustomFlaxBartForConditionalGeneration
    from transformers import BartTokenizer
    import jax
    import random
    from tqdm.notebook import tqdm, trange
    import gc
    print("check point-1.1")   
    # make sure we use compatible versions
    DALLE_REPO = 'flax-community/dalle-mini'
    print("check point-1.2")   
    DALLE_COMMIT_ID = '4d34126d0df8bc4a692ae933e3b902a1fa8b6114'
    print("check point-1.3")   
    # set up tokenizer and model
    # tokenizer = BartTokenizer.from_pretrained(DALLE_REPO, revision=DALLE_COMMIT_ID)
    print("check point-1.5")   
    # model = CustomFlaxBartForConditionalGeneration.from_pretrained(DALLE_REPO, revision=DALLE_COMMIT_ID)
    print("hi-1")
    # set a prompt.
    # prompt = 'On either side the river lie Long fields of barley and of rye, That clothe the wold and meet the sky; And thro the field the road runs by To many-towerd Camelot.'
    # prompt = 'water'

    # tokenize the prompt
    tokenized_prompt = tokenizer(prompt, return_tensors='jax', padding='max_length', truncation=True, max_length=128)
    tokenized_prompt

    """Notes:

    * `0`: BOS, special token representing the beginning of a sequence
    * `2`: EOS, special token representing the end of a sequence
    * `1`: special token representing the padding of a sequence when requesting a specific length
    """

    print("hi0")
    # n_predictions = 1 # 8 # for speed

    # create random keys
    seed = random.randint(0, 2**32-1) # 32
    key = jax.random.PRNGKey(seed)
    subkeys = jax.random.split(key, num=n_predictions)
    subkeys

    # generate sample predictions
    encoded_images = [model.generate(**tokenized_prompt, do_sample=True, num_beams=1, prng_key=subkey) for subkey in tqdm(subkeys)]
    encoded_images[0]

    """The first token (`16384`) is a special token representing the start of a sequence in the decoder (not part of the image codebook)."""

    # remove first token (BOS)
    encoded_images = [img.sequences[..., 1:] for img in encoded_images]
    encoded_images[0]

    """The generated images are now represented by 256 tokens."""

    encoded_images[0].shape

    """## Decode images

    The generated images need to be decoded with `flax-community/vqgan_f16_16384`.
    """
    print("hi1")
    from vqgan_jax.modeling_flax_vqgan import VQModel
    import numpy as np
    from PIL import Image

    # make sure we use compatible versions
    VQGAN_REPO = 'flax-community/vqgan_f16_16384'
    VQGAN_COMMIT_ID = '90cc46addd2dd8f5be21586a9a23e1b95aa506a9'

    # set up VQGAN
    vqgan = VQModel.from_pretrained(VQGAN_REPO, revision=VQGAN_COMMIT_ID)

    # decode images
    decoded_images = [vqgan.decode_code(encoded_image) for encoded_image in tqdm(encoded_images)]
    decoded_images[0]

    # normalize images
    clipped_images = [img.squeeze().clip(0., 1.) for img in decoded_images]

    # convert to image
    images = [Image.fromarray(np.asarray(img * 255, dtype=np.uint8)) for img in clipped_images]

    # display an image
    images[0]

    """## Rank images with CLIP

    We use `openai/clip-vit-base-patch32` to rank generated images against the prompt.
    """
    print("hi3")
    from transformers import CLIPProcessor, FlaxCLIPModel

    # set up model and processor
    # clip = FlaxCLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    # processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    """The CLIP processor tokenizes text and pre-processes images (resize to 224x224 and normalize) as required per the CLIP model."""
    # print("hi3")
    # evaluate scores
    inputs = processor(text=prompt, images=images, return_tensors='np')
    logits = clip(**inputs).logits_per_image
    scores = jax.nn.softmax(logits, axis=0).squeeze()  # normalize and sum all scores to 1



    from IPython.display import display
    # rank images by score
    print(f'Prompt: {prompt}\n')
    for idx in scores.argsort()[::-1]:
        print(f'Score: {scores[idx]}')
        display(images[idx])
        images[idx].save("static/"+prompt+"_"+str(idx) +".png","PNG")

        # print()

    # del DALLE_REPO , DALLE_COMMIT_ID , tokenizer, model
    # gc.collect()
    return

if __name__ == "__main__":
    from dalle_mini.model import CustomFlaxBartForConditionalGeneration
    from transformers import BartTokenizer
    from transformers import CLIPProcessor, FlaxCLIPModel
    DALLE_REPO = 'flax-community/dalle-mini'
    DALLE_COMMIT_ID = '4d34126d0df8bc4a692ae933e3b902a1fa8b6114'
    tokenizer = BartTokenizer.from_pretrained(DALLE_REPO, revision=DALLE_COMMIT_ID)
    model = CustomFlaxBartForConditionalGeneration.from_pretrained(DALLE_REPO, revision=DALLE_COMMIT_ID)
    clip = FlaxCLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    getSaveImagesRepresentingTask("a boat fighting the storm",4,tokenizer,model,clip,processor)