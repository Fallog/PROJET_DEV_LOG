from typing import Any

import numpy as np
import torch.nn as nn
import torch
from PIL import Image
from copy import deepcopy
from numpy import ndarray
from torch import Tensor

from database import request_data_by_id
from torchvision import transforms
import autoencoder as ae


def flatten_img(img_path: str | list[str], img_type="tensor", encode=False)\
        -> Tensor | ndarray:
    """Uses the path stored in img_path to create a Tensor or a ndarray
    in a convenient shape for all the future modifications.
    This function can also encode the image if needed

    Parameters
    ----------
    img_path: str or list[str]
        Path or paths of the images to be retrieved
    img_type: str
        Specifies the type of the object to be returned
    encode: bool
        True if the images need to be encoded by the autoencoder,
        False otherwise

    Returns
    -------
    flat_img: torch.Tensor or numpy.ndarray
    Contains the values for all the pixels of the images found in the
    given path. If several paths are given, all the images are stored
    in one single object

    >>>arr = np.array([3, 6, 9])
    >>>flatten_img(arr).shape
    (3, 54)

    >>> tensor = torch.Tensor([3, 5, 8])
    >>>flatten_img(tensor).size()
    torch.Size([3, 40])


    """
    if img_type == "tensor":
        # To transform a numpy array or a PIL image to a torch Tensor
        to_tensor = transforms.ToTensor()
        # To flatten a torch tensor to a tensor with one dimension x number of color channels
        flatten = nn.Flatten(1, 2)

        if type(img_path) is list:
            temp_img = Image.open(img_path[0])  # Temporary img to get its size
            temp_tensor = to_tensor(temp_img)
            size = temp_tensor.shape

            # Global Tensor containing all the images
            flat_img_tensor = torch.zeros((len(img_path), size[0],
                                           size[1] * size[2]))
            # print(f"Global tensor shape: {flat_img_tensor.shape}")
            for i, path in enumerate(img_path):
                if type(path) is str:
                    img = Image.open(path)  # PIL picture

                    if encode:
                        # TODO Aller chercher un autoencoder entraîné pour encoder les photos
                        img = ae.encode()

                    img_tensor = to_tensor(img)  # Transform PIL to torch Tensor
                    # print(f"Image tensor shape: {img_tensor.shape}")
                    flat_img_tensor[i] = flatten(img_tensor)

                else:
                    raise TypeError("List should contain paths (str)")
            return flat_img_tensor

        elif type(img_path) is str:
            img = Image.open(img_path)  # PIL picture

            if encode:
                # TODO Aller chercher un autoencoder entraîné
                img = ae.encode()

            img_tensor = to_tensor(img)
            return flatten(img_tensor)

        else:
            raise TypeError("Input should either be a path (str)\
                or a list of paths")

    elif img_type == "numpy":
        if type(img_path) is list:
            flat_img_list = [0] * len(img_path)
            for i, path in enumerate(img_path):
                if type(path) is str:
                    img = Image.open(path)  # PIL picture

                    if encode:
                        # TODO Aller chercher un autoencoder entraîné
                        img = ae.encode()

                    img_arr = np.array(img)
                    flat_img_list[i] = np.concatenate(img_arr)

                else:
                    raise TypeError("List should contain paths (str)")
            return np.array(flat_img_list)

        elif type(img_path) is str:
            img = Image.open(img_path)  # PIL picture

            if encode:
                # TODO Aller chercher un autoencoder entraîné
                img = ae.encode()
                img = img.numpy()

            img_arr = np.transpose(np.array(img), (2, 0, 1))  # Uniformisation of the data dimension
            print(f"Array of the img is: {img_arr.shape}")
            return img_arr.reshape(img_arr.shape[0], -1)

        else:
            raise TypeError("Input should either be a path (str)\
                or a list of paths")

    else:
        raise ValueError("Wrong parameter img_type value. Should either\
                         be tensor or numpy")


def mutate_img(img_encoded: ndarray | Tensor, mutation_rate: float = 0.2,
               noise: float = 1, mut_type="random") -> ndarray | Tensor:
    """Slightly modifies a or several images given in a ndarray or a
    Tensor with random noise.

    Parameters
    ----------
    img_encoded: numpy.ndarray or torch.Tensor
        Object containing an or several images pixels values
    mutation_rate: float
        Probability for a pixel to be modified
    noise: float
        Strength of the random noise, coefficient multiplying the noise
    mut_type: str
        Either random or uniform. If uniform every pixel is perturbed
        with a Gaussian random noise. If random, the pixels to be
        modified are randomly chosen according to mutation_rate

    Returns
    -------
    img_mut: numpy.ndarray or torch.Tensor
        Image or images built on img_encoded with Gaussian random noise
        added to it

    >>>tensor = torch.randn((3, 3))
    tensor([[-3.3558,  1.5579, -0.2904],
        [-0.2572, -0.7410, -0.8748],
        [ 1.2381, -0.4762,  0.3762]])
    >>>mutate_img(tensor, mut_type='uniform')
    tensor([[-3.6974,  1.9027, -0.6431],
        [-0.0740,  0.5979, -1.3189],
        [ 0.7544, -1.8443,  0.2005]])
    >>>mutate_img(tensor, mutation_rate=0.4)
    tensor([[-3.3558,  1.5579, -0.2904],
        [-0.2572, -0.7410, -0.8748],
        [ 1.8747, -0.3136,  0.4488]])
    """
    # Randomly selects the pixels to be modified
    if mut_type == "random":
        if type(img_encoded) is ndarray:
            img_encoded: ndarray
            # Random draw for each pixel of img_encoded
            mut_proba_arr = np.random.random(size=img_encoded.shape)
            img_mut = img_encoded
            noise_arr = noise * np.random.normal(size=img_encoded.shape)
            # Adding noise only on pixels where mut_proba_arr is lower than mutation_rate
            img_mut[mut_proba_arr < mutation_rate] += noise_arr[mut_proba_arr < mutation_rate]

        elif type(img_encoded) is Tensor:
            img_encoded: Tensor
            mut_proba_tensor = torch.rand(size=img_encoded.size())
            img_mut = img_encoded
            noise_tensor = noise * torch.randn(size=img_encoded.size())
            img_mut[mut_proba_tensor < mutation_rate] += noise_tensor[mut_proba_tensor < mutation_rate]

        else:
            raise TypeError(f"Input should either be of type np.ndarray \
                or torch.Tensor and not a {type(img_encoded)}")

        return img_mut

    # Modify every pixel with a random noise
    elif mut_type == "uniform":
        # Add random noise on each pixel
        if type(img_encoded) is np.ndarray:
            img_encoded: ndarray
            # Adding white noise to the numpy array
            img_mut = img_encoded + noise \
                * np.random.normal(size=img_encoded.shape)

        elif type(img_encoded) is torch.Tensor:
            img_encoded: Tensor
            # Adding white noise to a torch Tensor
            img_mut = img_encoded + noise \
                * torch.randn(size=img_encoded.size())

        else:
            raise TypeError(f"Input should either be of type np.ndarray \
                or torch.Tensor and not a {type(img_encoded)}")

        return img_mut

    else:
        raise ValueError("Chose a valid value for the modif parameter")


def crossing_over(images_encoded: ndarray | Tensor,
                  crossing_rate: float) -> ndarray | Tensor:
    """Swaps pixels between the given input images. Swaps are made
    randomly for each pixels.

    Parameters
    ----------
    images_encoded: numpy.ndarray or torch.Tensor
        Object containing an or several images pixels values. The images
        where the pixel are drawn is chosen randomly between all the
        input images, with a uniform distribution
    crossing_rate: float
    Probability for a pixel to be swapped between images

    Returns
    -------
    new_img: numpy.ndarray or torch.Tensor
        Image or images on which the crossing-overs are performed

    # TODO Test de code pour les crossing over
    """
    if type(images_encoded) is ndarray:
        images_encoded: ndarray
        for i, img in enumerate(images_encoded):
            crossing_arr = np.random.random(size=img.shape)
            # Randomly choosing which image to swap pixels with
            other_ind = [j for j in range(images_encoded.shape[0]) if j != i]
            chosen_ind = np.random.choice(other_ind)

            new_img = deepcopy(img)
            # Swapping
            new_img[crossing_arr < crossing_rate] = images_encoded[chosen_ind][crossing_arr < crossing_rate]
            return new_img

    elif type(images_encoded) is Tensor:
        images_encoded: Tensor
        for i, img in enumerate(images_encoded):
            crossing_tensor = torch.rand(size=img.size())

            # Randomly choosing which image to swap pixels with
            other_ind = [k for k in range(images_encoded.size()[0]) if k != i]
            chosen_ind = np.random.choice(other_ind)

            new_img = deepcopy(img)
            # Swapping
            new_img[crossing_tensor < crossing_rate] = images_encoded[chosen_ind][crossing_tensor < crossing_rate]
            return new_img

    else:
        raise TypeError(f"Input should either be of type np.ndarray \
            or torch.Tensor and not a {type(images_encoded)}")


if __name__ == "__main__":
    env_path = "./projet"

    id_nb = 20
    # Path of the 20th image
    pic_path = request_data_by_id(env_path, id_nb)
    print(f"Path for the picture(s): {pic_path}")

    # Path of the first 20 images
    id_array = np.arange(start=0, stop=20, step=1)
    pic_path_list = request_data_by_id(env_path, id_array)

    # Open the image with PIL
    pic = Image.open(pic_path)
    print(f"Type of the picture: {type(pic)}")

    # Convert the image into a ndarray
    pic_array = np.array(pic)
    # print(f"Array of the pixels: {pic_array}")
    print(f"Shape of the pic: {pic_array.shape}")

    # Testing flatten func for ndarray
    print(f"Flat ndarray shape: {flatten_img(pic_path, 'numpy').shape}")
    print(f"Flat ndarray list shape: {flatten_img(pic_path_list, 'numpy').shape}")
    print(f"Shape of first element: {flatten_img(pic_path_list, 'numpy')[0].shape}")

    # Transform the image into a torch Tensor object
    to_tensor = transforms.ToTensor()
    pic_tensor = to_tensor(pic_array)
    print(f"Base Tensor dim: {pic_tensor.shape}")

    # Testing flatten func for Tensor
    flat_pic = flatten_img(pic_path)
    print(f"Tensor dim after flatten func: {flat_pic.shape}")
    flat_pics = flatten_img(pic_path_list)
    print(f"Tensor list dim after flatten: {flat_pics.shape}")

    # Trying with oliveti dataset
    oliveti_faces = ae.faces.images  # ndarray of all the pictures
    fst_face = oliveti_faces[0]
    a_tensor = to_tensor(fst_face)
    print(f"Olivetti shape: {a_tensor.shape}")

    # Create an autoencoder
    autoencoder = ae.Autoencoder()

    # Encoding an image
    pic_encoded = ae.encode(autoencoder, fst_face)
    print(f"Shape of the encoded tensor: {pic_encoded.shape}")

    # Testing mutation on all pixels
    some_tensor = torch.randn(size=(3, 3))
    print(f"Base tensor: {some_tensor}")
    print(f"Mutated tensor: {mutate_img(some_tensor, mut_type='uniform')}")

    some_array = np.random.randn(3, 3)
    print(f"Base array: {some_array}")
    print(f"Mutated array: {mutate_img(some_array, mut_type='uniform')}")

    # Testing mutation on random pixels
    mut_tensor_rdm = mutate_img(some_tensor, mutation_rate=0.2)
    print(f"Mutated tensor (random): {mut_tensor_rdm}")
    mut_arr_rdm = mutate_img(some_array, mutation_rate=0.2)
    print(f"Mutated array (random): {mut_arr_rdm}")
