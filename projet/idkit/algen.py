import os.path

import numpy as np
import torch.nn as nn
import torch
from PIL import Image
from PIL import ImageFilter
from torch import Tensor
from torchvision import transforms

import utils
from database import request_data_by_id
import autoencoder_deploy as ae


def flatten_img(img_path, env_path):
    """Uses the path stored in img_path to create a Tensor in a smaller
    dimension for the future mutations and crossing-overs.
    This function also encodes the image retrieved from the given path.

    Parameters
    ----------
    img_path: str or list[str]
        Path or paths of the images to retrieve
    env_path: str
        Path of the current environment, used to retrieve the
        autoencoder trained model

    Returns
    -------
    flat_img: torch.Tensor
        Contains the values for all the pixels of the images found in the
        given path. If several paths are given, all the images are stored
        in one single Tensor

    >>>path = "./projet/env/Database/img_dataset/celeba/img_align_celeba/000021.jpg"
    >>>Image.open(path).size
    >>>flatten_img(path).size()
    torch.Size([64, 324])

    >>>path_list = ['./projet/env/Database/img_dataset/celeba/img_align_celeba/000001.jpg',
    >>>             './projet/env/Database/img_dataset/celeba/img_align_celeba/000002.jpg',
    >>>             './projet/env/Database/img_dataset/celeba/img_align_celeba/000003.jpg']
    >>>flatten_img(path_list).size()
    torch.Size([3, 64, 324])
    """
    # Path where to find a trained autoencoder
    model_path = os.path.join(utils.get_path(env_path, "Encoder"),
                              "model.pt")
    autoencoder = ae.load_model(model_path)  # Loading the trained autoencoder

    # To transform a PIL image to a torch Tensor
    to_tensor = transforms.ToTensor()
    # To flatten a torch tensor to a tensor with two dimensions only
    flatten = nn.Flatten(1, 2)

    if type(img_path) is list:
        temp_img = Image.open(img_path[0])  # Temporary img to get its size
        temp_tensor = to_tensor(temp_img)
        temp_tensor = ae.crop_image_tensor(temp_tensor)
        temp_tensor = ae.encode(autoencoder, temp_tensor)
        size = temp_tensor.shape

        # Global Tensor containing all the images
        flat_img_tensor = torch.zeros((len(img_path), size[0],
                                       size[1] * size[2]))

        for i, path in enumerate(img_path):
            if type(path) is str:
                img = Image.open(path)  # PIL Image
                img_tensor: Tensor = to_tensor(img)  # Image -> Tensor

                if img_tensor.size() == torch.Size((3, 218, 178)):
                    # Cropping the tensor to 160x160 pixels
                    img_tensor_crop = ae.crop_image_tensor(img_tensor)

                else:
                    img_tensor_crop = img_tensor

                encoded_tensor = ae.encode(autoencoder, img_tensor_crop)

                flat_img_tensor[i]: Tensor = flatten(encoded_tensor)

            else:
                raise TypeError("List should contain paths (str)")

        return flat_img_tensor

    elif type(img_path) is str:
        img = Image.open(img_path)  # PIL Image
        img_tensor = to_tensor(img)  # Image -> Tensor

        # Cropping the tensor to 160x160 pixels
        img_tensor_crop = ae.crop_image_tensor(img_tensor)

        encoded_tensor: Tensor = ae.encode(autoencoder, img_tensor_crop)
        flat_tensor: Tensor = flatten(encoded_tensor)

        return flat_tensor

    else:
        raise TypeError("Input should either be a path (str)\
            or a list of paths")


def deflatten_img(flat_tensor, base_encoded_dim, env_path):
    """Resize a Tensor containing one or several encoded images into the
    specified size then decode it using the trained model.

    Parameters
    ----------
    flat_tensor: torch.Tensor
        Tensor containing the encoded version of one or several images.
    base_encoded_dim: tuple of ints
        Size of the tensor before going into flatten_img function.
    env_path: str
        Path of the current environment, used to retrieve the
        autoencoder trained model

    Returns
    -------
    decoded_img: PIL.Image
        Decoded version of the image
    or
    img_list: list[PIL.Image]
        Decoded versions of the images

    >>>tensor = torch.randn((64, 324))
    >>>deflatten_img(tensor, torch.Size((64, 18, 18))).size
    (160, 160)
    """
    # Path where to find a trained autoencoder
    model_path = os.path.join(utils.get_path(env_path, "Encoder"), "model.pt")
    autoencoder = ae.load_model(model_path)  # Loading the trained autoencoder

    if flat_tensor.dim() == 2:
        # Reform the original encoded tensor
        unflat_tensor = flat_tensor.reshape(base_encoded_dim)

        decoded_img = ae.decode(autoencoder, unflat_tensor)

        return decoded_img

    elif flat_tensor.dim() == 3:
        # Creating a list for the images
        img_list = [0] * flat_tensor.size()[0]

        for i, flat_img in enumerate(flat_tensor):
            # Reform the original encoded tensor
            unflat_img = flat_img.reshape(base_encoded_dim)

            decoded_img = ae.decode(autoencoder, unflat_img)

            img_list[i] = decoded_img

        return img_list

    else:
        raise Exception(f"Wrong tensor dimension. Expected: 2 or 3, got\
                        {flat_tensor.dim()}")


def mutate_img(tensor_encoded, mutation_rate=0.05, mode='add', scale='partial'):
    """Slightly modifies a or several images given in a Tensor.
    The modifications can be classic random noise or specific pixel
    reconstruction according to the tensor mean and standard deviation.

    Parameters
    ----------
    tensor_encoded: torch.Tensor
        Tensor containing one or several images pixels values.
    mutation_rate: float
        Probability for a pixel to be modified.
    scale: str
        Either 'partial' or 'total'. If 'total' than every pixel is
        perturbed with a Gaussian random noise. If 'partial' than the
        modified pixels are randomly chosen according to mutation_rate.
        Default to 'partial'.
    mode: str
        Either 'add' or 'reconstruct'.
        Specifies the type of modifications to perform. If 'add' than
        the noise is added to chosen tensor values. The noise is a
        random number drawn from a gaussian distribution with mean 0
        and a standard deviation of 1. If 'reconstruct' than the tensor
        is rebuilt

    Returns
    -------
    img_mut: torch.Tensor
        Image or images built on img_encoded with Gaussian random noise
        added to it.

    >>>a = torch.randn((3, 3))
    tensor([[-0.2015,  0.4780,  1.1307],
        [ 1.6018,  0.4684,  0.2649],
        [ 1.0546,  1.3608,  0.6707]])
    >>>mutate_img(a, mode='add', scale='total')
    tensor([[-3.3558,  1.5579, -0.2904],
        [-0.2572, -0.7410, -0.8748],
        [ 1.8747, -0.3136,  0.4488]])
    >>>b = torch.zeros((3, 3)) + 2
    tensor([[ 3.5582,  4.3696,  1.3062],
        [-0.6573,  3.4122,  1.5021],
        [ 5.4977,  2.1273,  2.0095]])
    >>>mutate_img(a, mode='reconstruct', scale='partial')
    tensor([[ 4.7168,  4.3696,  1.3062],
        [-0.6573,  3.4122,  1.5021],
        [ 6.6994,  1.3877, -0.0979]])
    """
    if type(tensor_encoded) is Tensor:
        if tensor_encoded.dim() == 2:
            img_mut = tensor_encoded
            if mode == 'add':
                # Add random noise to random pixels
                if scale == 'partial':
                    # Randomly selects the pixels to be modified
                    mut_proba_tensor = torch.rand(size=tensor_encoded.size())
                    noise_tensor = torch.randn(size=tensor_encoded.size())
                    img_mut[mut_proba_tensor < mutation_rate] += noise_tensor[mut_proba_tensor < mutation_rate]

                # Add random noise on each pixel
                elif scale == 'total':
                    # Adding white noise to all the tensor values
                    img_mut += torch.randn(size=tensor_encoded.size())

                else:
                    raise ValueError(f"Wrong value for the scale parameter. \
                    Expected 'partial' or 'total' got {scale} instead")

            # Building a new tensor based on the mean and deviation
            # of the input tensor
            elif mode == 'reconstruct':
                mu = tensor_encoded.mean()
                std = tensor_encoded.std()

                if scale == 'partial':
                    # Randomly selects the pixels to be modified
                    mut_proba_tensor = torch.rand(size=tensor_encoded.size())
                    # Size of the selected region
                    selected_size = img_mut[mut_proba_tensor < mutation_rate].size()
                    # Reconstruction of the selected region
                    img_mut[mut_proba_tensor < mutation_rate] = mu \
                        + torch.randn(selected_size) * std

                elif scale == 'total':
                    # Reconstruction of the whole tensor
                    img_mut = mu + torch.randn(tensor_encoded.size()) * std

                else:
                    raise ValueError(f"Wrong value for the scale parameter. \
                    Expected 'partial' or 'total' got {scale} instead")

            else:
                raise ValueError(f"Wrong value for the mode parameter. \
                Expected 'add' or 'reconstruct' got {mode} instead")

            return img_mut

        elif tensor_encoded.dim() == 3:
            global_tensor = torch.zeros(tensor_encoded.size())
            for i, tensor in enumerate(tensor_encoded):
                img_mut = tensor
                # Adding gaussian noise to the tensors
                if mode == 'add':
                    # Act on random values
                    if scale == 'partial':
                        # Randomly selects the pixels to be modified
                        mut_proba_tensor = torch.rand(size=tensor.size())
                        # Creating the gaussian noise
                        noise_tensor = torch.randn(size=tensor.size()) + img_mut

                        img_mut = torch.where(mut_proba_tensor < mutation_rate,
                                              noise_tensor, img_mut)
                    # Act on every value
                    elif scale == 'total':
                        # Adding white noise to all the tensor values
                        img_mut = img_mut + torch.randn(size=tensor.size())

                    else:
                        raise ValueError(f"Wrong value for the scale parameter. \
                        Expected 'partial' or 'total' got {scale} instead")

                # Building a new tensor based on the mean and deviation
                # of the input tensor
                elif mode == 'reconstruct':
                    mu = tensor.mean()
                    std = tensor.std()

                    if scale == 'partial':
                        # Randomly selects the pixels to be modified
                        mut_proba_tensor = torch.rand(size=tensor.size())
                        # Reconstructed tensor
                        recons_tensor = mu + torch.randn(tensor.size()) * std
                        # Reconstruction of the selected region
                        img_mut = torch.where(mut_proba_tensor < mutation_rate,
                                              recons_tensor, img_mut)

                    elif scale == 'total':
                        # Reconstruction of the whole tensor
                        img_mut = mu + torch.randn(tensor.size()) * std

                else:
                    raise ValueError(f"Wrong value for the mode parameter. \
                    Expected 'add' or 'reconstruct' got {mode} instead")

                global_tensor[i] = img_mut

            return global_tensor

        else:
            raise TypeError(f"Wrong Tensor dimension, expected 2 or 3, \
                            having {tensor_encoded.dim()}")

    else:
        raise TypeError(f"Input should be of type or torch.Tensor \
                        and not a {type(tensor_encoded)}")


def chose_closest_tensor(input_tensor, other_tensors):
    """Returns a sub-tensor inside other_tensors that is the closest, in
    terms of euclidian distance of its value, to input_tensor.

    Parameters
    ----------
    input_tensor: torch.Tensor
        Tensor object.
    other_tensors: torch.Tensor
        Bigger tensor containing two tensors of the same dimension as
        input_tensor.

    Returns
    -------
    closest_tensor: torch.Tensor
        Closest Tensor to input_tensor, same size as input_tensor

    >>>a = torch.randn((3, 3)) + 2
    tensor([[-1.1437, -0.4471,  0.8246],
        [-0.8996,  0.2804,  0.7916],
        [-0.0613,  0.1011, -1.1687]])
    >>>b = torch.randn(3, 3) + 3
    tensor([[3.3959, 2.4724, 2.4523],
        [3.1876, 3.6320, 4.1872],
        [3.4574, 2.3627, 3.7312]])
    >>>c = torch.randn(3, 3) + 7
    tensor([[6.9013, 6.2670, 6.6347],
        [7.2425, 6.0343, 6.7958],
        [7.7789, 8.6575, 8.1256]])
    >>>d = torch.cat([b.unsqueeze(0), c.unsqueeze(0)], 0)
    >>>chose_closest_tensor(a, d)
    tensor([[3.3959, 2.4724, 2.4523],
            [3.1876, 3.6320, 4.1872],
            [3.4574, 2.3627, 3.7312]])
    """
    # Computing euclidian distance between input and the other tensors
    dist_list = [torch.dist(input_tensor, t, p=2) for t in other_tensors]
    dist_tensor = Tensor(dist_list)
    # Choosing the tensor that has the closest distance to input_tensor
    closest_tensor = other_tensors[torch.argmin(dist_tensor)]
    return closest_tensor


def crossing_over(tensor_encoded, crossing_rate):
    """Swaps pixels between the given input images. Swaps are made
    randomly for each pixel but the choice of which images are to be
    swapped is made based on a mean distance criterion.

    Parameters
    ----------
    tensor_encoded: torch.Tensor
        Tensor containing several images pixels values. The image
        where the pixel are drawn is chosen randomly between all the
        input images, with a uniform distribution
    crossing_rate: float
        Probability for a pixel to be swapped between images

    Returns
    -------
    new_tensor: torch.Tensor
        Image or images on which the crossing-overs were performed

    >>>a = torch.randn((2, 3, 3))
    tensor([[[-0.1689, -1.0904, -0.6837],
         [ 0.7088,  1.5056, -1.0236],
         [ 0.9674, -1.3691,  0.3151]],
        [[-1.3492,  1.3077, -0.3023],
         [-0.2509,  0.4455, -1.4012],
         [ 0.2429, -0.4856, -1.4789]]])
    >>>crossing_over(a, crossing_rate=0.3)
    tensor([[[-1.3492, -1.0904, -0.6837],
         [ 0.7088,  1.5056, -1.4012],
         [ 0.9674, -1.3691,  0.3151]],

        [[-1.3492,  1.3077, -0.3023],
         [-0.2509,  1.5056, -1.4012],
         [ 0.9674, -1.3691,  0.3151]]])
    """
    if type(tensor_encoded) is Tensor:
        global_tensor = torch.zeros(tensor_encoded.size())
        for i, tensor in enumerate(tensor_encoded):
            # List of booleans, True when it is not tensor
            is_not_this_tensor = [True if not torch.equal(tensor, t)
                                  else False for t in tensor_encoded]
            # Sub-tensor containing all the tensors inside tensor_encoded
            # except tensor
            other_tensor = tensor_encoded[Tensor(is_not_this_tensor).bool()]
            # Chose the closest tensor to tensor in terms of euclidian
            # distance. It values will be swapped with tensor values
            chosen_tensor = chose_closest_tensor(tensor, other_tensor)
            # Randomly chose the tensor values that will be swapped
            is_crossing = torch.rand(chosen_tensor.size()) < crossing_rate
            # Perform the swapping
            crossed_tensor = torch.where(is_crossing, chosen_tensor, tensor)

            global_tensor[i] = crossed_tensor

        return global_tensor

    else:
        raise TypeError(f"Input should be of type torch.Tensor \
                        and not a {type(tensor_encoded)}")


def remove_worst_tensor(input_tensor):
    """Returns a truncated version of the input_tensor where the tensor
    that has the greatest euclidian distance with the other is removed

    Parameters
    ----------
    input_tensor: Tensor
        Tensor object with 3 dimensions

    Returns
    -------
    good_tensors: Tensor
        Tensor object with 3 dimensions as well but where the tensor
        with the greatest euclidian distance was removed
    >>>a = torch.randn((3, 3)) + 2.3
    tensor([[1.6615, 0.7543, 1.6239],
        [2.6538, 2.8430, 1.9353],
        [2.1524, 1.5966, 2.4236]])
    >>>b = torch.randn((3, 3)) + 12.9
    tensor([[16.6363, 13.5585, 14.8932],
        [12.5578, 12.4041, 13.0811],
        [11.1850, 14.0882, 12.0674]])
    >>>c = torch.randn((3, 3)) + 5.43
    tensor([[6.7253, 3.4713, 7.6311],
        [3.7403, 4.5557, 5.5945],
        [5.8821, 6.7597, 6.3254]])
    >>>cat = torch.cat((a.unsqueeze(0), b.unsqueeze(0), c.unsqueeze(0)), 0)
    >>>remove_worst_tensor(cat)
    tensor([[[1.6615, 0.7543, 1.6239],
         [2.6538, 2.8430, 1.9353],
         [2.1524, 1.5966, 2.4236]],

        [[6.7253, 3.4713, 7.6311],
         [3.7403, 4.5557, 5.5945],
         [5.8821, 6.7597, 6.3254]]])
    """
    # Tensor to store the total distance from each tensor to the other
    dist_tensor = torch.zeros(input_tensor.size()[0])
    for i, tensor in enumerate(input_tensor):
        # Compute euclidian distance to the other tensors
        dist_tensor[i] = torch.dist(tensor, input_tensor)
    # List of boolean, False for the maximum of dist_tensor
    is_kept = [False if i == torch.argmax(dist_tensor) else True
               for i in range(input_tensor.size()[0])]
    # Transform to boolean tensor
    bool_tensor = Tensor(is_kept).bool()
    good_tensors = input_tensor[bool_tensor]
    return good_tensors


def create_new_images(img_path, env_path):
    """Generates 5 new images based on the 3 given with img_path.
    It uses the crossing_over function to generate 6 new images by
    swapping the values between the encoded tensors and then remove the
    worst one in terms of euclidian distance with the others

    Parameters
    ----------
    img_path: list of str
        Path where to retrieve the selected images. These images are
        used to create 5 new images with crossing-overs
    env_path: str
        Path of the current environment, used to save the generated
        images at the correct place

    Returns
    -------
    True to indicate to the interface that the image are generated
    """
    img_encoded_tensor = flatten_img(img_path, env_path)
    # Create 3 new images with crossing-overs
    crossed_img = crossing_over(img_encoded_tensor, crossing_rate=0.5)
    # Create 3 more images with crossing-overs
    more_crossing = crossing_over(img_encoded_tensor, crossing_rate=0.5)
    # Concatenation of the 6 tensors
    new_tensors = torch.cat((crossed_img, more_crossing), dim=0)
    # Keep the 5 best images in terms of deviation
    good_5_tensors = remove_worst_tensor(new_tensors)
    # Decoding and converting to PIL Images
    new_images = deflatten_img(good_5_tensors, (64, 18, 18), env_path)
    # Saving the generated pictures
    for i, img in enumerate(new_images):
        name = f"image{i}.png"
        path = utils.get_path(env_path, 'gen_img') + "/" + name
        img.save(path)

    return True


if __name__ == "__main__":
    env_path = "./projet"

    # Choosing 3 random images in the database
    random_id = np.random.randint(low=0, high=600, size=(3,))
    # print(random_id)
    random_img_path = request_data_by_id(env_path, random_id)
    print(random_img_path)
    random_img_tensor = flatten_img(random_img_path, env_path)

    # Showing the 3 selected images
    for path in random_img_path:
        img = Image.open(path)
        img.show()

    # Mutating the images
    mut_rand_tensor = mutate_img(random_img_tensor, mutation_rate=0.1,
                                 mode='reconstruct', scale='partial')

    # Crossing-overs between the pictures
    crossed_tensors = crossing_over(random_img_tensor, crossing_rate=0.5)
    # crossed_tensors_mut = crossing_over(mut_rand_tensor, crossing_rate=0.4)
    deflat_sev = deflatten_img(crossed_tensors, (64, 18, 18), env_path)
    # deflat_sev_mut = deflatten_img(crossed_tensors_mut, (64, 18, 18), env_path)
    for img in deflat_sev:
        img.show()

    # for img in deflat_sev_mut:
    #     img.show()

    create_new_images(random_img_path, env_path)
