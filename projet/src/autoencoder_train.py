#device = torch.device("cpu")

import numpy as np
import torch
import torch.nn as nn
import torch.optim 
from torchsummary import summary
from torch.utils.data import TensorDataset, Dataset, DataLoader
import matplotlib.pyplot as plt
import os
from PIL import Image
import database
import torchvision.transforms as T
import torchvision.transforms.functional as TF
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split

from projet import utils                   

class Autoencoder(nn.Module):
    """
    A convolutional autoencoder neural network.

    The autoencoder has two main components: an encoder and a decoder. The encoder consists of a sequence of
    convolutional layers that encode the input image into a lower-dimensional latent space. The decoder takes the
    encoded representation and reconstructs the original image.

    Args:
        None

    Attributes:
        encoder (nn.Sequential): A sequence of convolutional layers that make up the encoder.
        decoder (nn.Sequential): A sequence of convolutional layers that make up the decoder.

    Methods:
        forward(x: torch.Tensor): Computes the forward pass of the autoencoder given an input tensor `x`. Returns the
        reconstructed output tensor.
    """
    def __init__(self):
        super(Autoencoder, self).__init__()

        # Encoder
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 16, 3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, 3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 7, stride=2, padding=1)
        )
        # Decoder
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(64, 32, 7, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(32, 16, 3, stride=2, padding=1, output_padding=1),
            nn.ReLU(),
            nn.ConvTranspose2d(16, 3, 3, stride=2, padding=1, output_padding=1),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

def load_model(path):
    """
    Loads the state dictionary of a PyTorch model from a file with the given name
    and returns the corresponding model object.

    Parameters:
        model (torch.nn.Module): PyTorch model to be loaded.
        path (str): Path to load the model from.

    Returns:
        torch.nn.Module: The loaded PyTorch model.
    """
    model = Autoencoder()
    model.load_state_dict(torch.load(path))
    return model

#################### Create a custom dataset class #########
class MyDataset(Dataset):
    """
    A PyTorch dataset that represents a collection of samples.

    Args:
        samples (torch.Tensor): A 4D tensor of shape (batch_size, height, width, channels) representing the samples.

    Attributes:
        samples (torch.Tensor): A 4D tensor of shape (batch_size, height, width, channels) representing the samples.

    Methods:
        __len__(): Returns the number of samples in the dataset.
        __getitem__(idx: int): Returns the sample at the given index.

    """
    def __init__(self, samples):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        return sample
################## Load Database ###########################
def load_dataset(width, height, nb_samples=-1, crop_images=False):
    """
    Loads image data from a folder and returns a PyTorch dataset object.

    parameters:
        width (int): The desired width of the images in pixels.
        height (int): The desired height of the images in pixels.
        nb_samples (int, optional): The maximum number of images to load from the folder. Defaults to -1, which loads all images.
        crop_images (bool, optional): Whether to crop the images to a fixed size. Defaults to False.

    Returns:
        MyDataset: A PyTorch dataset object containing the loaded image data.

    Raises:
        IOError: If the folder path is invalid or cannot be accessed.

    """
    # define crop parameters
    top = 40
    left = 18
    crop_height = 160
    crop_width = 160

    # Get a list of all image files in the input directory
    file_list = database.request_data_by_id(env_path, range(nb_samples))#, who= "Auto")

    # Save the total number of images in the folder
    total_nb_images = len(file_list)

    # Create a numpy array to hold the image data
    samples = np.zeros((len(file_list), height, width, 3), dtype=np.uint8)

    # Loop through the list of image files and load each image into the samples array
    for i, filename in enumerate(file_list):
        # Print a progress indicator every 10% of the way through the loop
        if i % (len(file_list)//10) == 0:
            print('-', end='', flush=True)
        # Load the image from disk
        im = Image.open(filename)
        # Convert the image data to a numpy array and add it to the samples array
        samples[i] = np.asarray(im)

    # Convert the numpy array to a PyTorch tensor, and normalize the pixel values to [0, 1]
    samples = torch.from_numpy(samples.astype(np.float32) / 255.0)

    # Crop the images if requested
    if crop_images:
        cropped_samples = torch.empty(samples.size(0), crop_height, crop_width, 3)
        for i, tensor in enumerate(samples):
            img = tensor
            img = img.permute(2, 0, 1)
            img = TF.crop(img, top, left, crop_height, crop_width)
            img = img.permute(1, 2, 0)
            cropped_samples[i] = img
        samples = cropped_samples

    # Remove the extra dimension from the tensor to make it a single tensor instead of a tuple
    samples = samples.squeeze()

    # Create a dataset object from the samples tensor
    dataset = MyDataset(samples)

    print(f"Number loaded images: {len(dataset)}/{total_nb_images}\n")

    return dataset

def crop_image_tensor(tensor):
    """
    Crops an image tensor to a fixed size.

    Parameters:
        tensor (torch.Tensor): A 3D tensor of shape (height, width, channels) representing an RGB image.

    Returns:
        torch.Tensor: A 3D tensor of shape (crop_height, crop_width, channels) representing the cropped image.

    """
    top = 40
    left = 18
    crop_height = 160
    crop_width = 160
    # img = tensor.permute(2, 0, 1)
    img = TF.crop(tensor, top, left, crop_height, crop_width)
    cropped_tensor = img.permute(1, 2, 0)
    # print(cropped_tensor.shape)
    return cropped_tensor

def plot_5_images(dataset, width, height):
    """
    Plots the 5 first images of the dataset
    Parameters:
        dataset (Dataloader): dataset
        width (int): width of the images
        height (int): height of the images
    """
    samples = dataset.samples

    fig, axs = plt.subplots(1, 5, figsize=(20,20))

    # if the image are flatten, reshape them to 2D images
    if len(samples.shape) == 2:
        print(samples.shape)
        samples = samples.reshape(-1, width, height, 3)

    # Draw 5 image number randomly
    random_indices = shuffle(np.arange(samples.shape[0]))[:5]

    for i in range(5):
        axs[i].imshow(samples[random_indices[i]], cmap=None, interpolation='nearest', aspect='equal')
        axs[i].axis("off")
    plt.show()

################### Data spliting  ##################
def split_train_valid_test_set(dataset, p_train, p_valid):
    """
    Splits the dataset into a training set and a validation 
    Parameters:
        dataset (Dataloader) : Dataset to be splited
        p_train (float) : Proportion of the total dataset for the training
        p_valid (float) : Proportion of the total dataset for the validation
    Returns:
    
    """
    samples = dataset.samples
    nb_samples = samples.shape[0]
    
    nb_test = (int) (nb_samples * (1-p_train))
    
    sample_train, sample_test = train_test_split(samples, test_size=nb_test)
    sample_train, sample_valid = train_test_split(sample_train, test_size=p_valid)

    print(f"training data : {sample_train.shape[0]}")
    print(f"validation data : {sample_valid.shape[0]}")
    print(f"test data: {sample_test.shape[0]}\n")

    train_ds = TensorDataset(sample_train.permute(0, 3, 1, 2))
    valid_ds = TensorDataset(sample_valid.permute(0, 3, 1, 2))
    test_ds = TensorDataset(sample_test.permute(0, 3, 1, 2))

    return train_ds.tensors[0], valid_ds.tensors[0], test_ds.tensors[0]

def test_train_model(model, train_loader, val_loader, nb_epochs, learning_rate):
    """
    Trains the autoencoder and plots the loss as a function of the numbers of epochs for 
    the validation and the training set
    Parameters:
        model (nn.Module): model to be trained
        train_loader (Dataloader): trainnig dataset 
        valid_loader (Dataloader): validation dataset 
    Returns:
        model (nn.Module): Trained Autoencoder model.
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = torch.nn.MSELoss()
    train_losses, val_losses = [], []
    device = "cpu"
    for epoch in range(nb_epochs):
        # Train the model
        model.train()
        train_loss = 0
        for data in train_loader:
            optimizer.zero_grad()
            inputs = data.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, inputs)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * inputs.size(0)
        train_loss /= len(train_loader.dataset)
        train_losses.append(train_loss)

        # Evaluate the model on the validation set
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for data in val_loader:
                inputs = data.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, inputs)
                val_loss += loss.item() * inputs.size(0)
        val_loss /= len(val_loader.dataset)
        val_losses.append(val_loss)

        # Print the loss for this epoch
        print(f'Epoch {epoch+1}/{nb_epochs}: Train Loss: {train_loss:.6f} Val Loss: {val_loss:.6f}')

    # Plot the training and validation losses over time
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.show()
    return(model)

def train_autoencoder(autoencoder, train_dl, nb_epochs, learning_rate):
    """
    Trains an Autoencoder model on the provided dataset for a specified number of epochs and learning rate.
    Parameters:
        autoencoder (nn.Module) : Model to be trained
        train_dl(Dataloader) : Dataset containing the images to be used for training.
        nb_epochs (int): The number of epochs to train the model for.
        learning_rate (float): learning rate parameters to chose for the training. 
    Returns:
        Autoencoder (nn.Module): Trained Autoencoder model.
    """
    # Define the loss function and optimizer
    loss_fn = torch.nn.MSELoss()
    optimizer = torch.optim.Adam(autoencoder.parameters(), lr=learning_rate)

    # Train the autoencoder for the specified number of epochs
    train_losses = []
    for epoch in range(nb_epochs):
        epoch_loss = 0
        for x in train_dl:
            x_hat = autoencoder(x)
            # print(x_hat.shape)
            loss = loss_fn(x_hat, x)
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            epoch_loss += loss.item()

        train_losses.append(epoch_loss / len(train_dl))
        print(f"Epoch {epoch + 1}/{nb_epochs}, loss={train_losses[-1]:.5f}")

    return autoencoder


# Recap of the Tensor sizes
"""
print("Database Tensor: ",CelebA[0].shape)
aTensor = CelebA[0]
x = aTensor.unsqueeze(0)
x = x.permute(0, 3, 1, 2)
print("Permuted Database Tensor: ",x.shape)
recon = AutoEncoder.encoder(x)
print("Encoded Tensor Shape: ",recon.shape)
decoded = AutoEncoder.decoder(recon)
print("Decoded Tensor : ",decoded.shape)
decoded2 = decoded.squeeze(0)
print("Decoded Tensor with the batch dimension erased: ", decoded2.shape)
"""

def encode(model, image: Image):
    """
    Encodes an input image using the given PyTorch model.
    Parameters:
        model (nn.Module): Neural networt model.
        image: torch.Tensor
            PIL Image object representing the input image.

    Returns:
        torch.Tensor: Tensor representing the encoded representation of the input image.
    """
    x = image.unsqueeze(0)  # Adding one dimension for the autoencoder
    # Changing the image to the correct dimensions order for the autoencoder
    x = x.permute(0, 3, 1, 2)
    encoded = model.encoder(x)
    return encoded[0]

def decode (encoded_tensor):
    decoded = model.decoder(encoded_tensor)
    decoded_shor = decoded.squeeze(0)
    return (decoded_shor)

if __name__ == "__main__":
    # env_path = os.path.dirname(os.path.realpath(__file__))
    env_path = "projet"

    CelebA_ds_tensor_path = os.path.join(utils.get_path(env_path, "Encoder"), "database_tensor.npy")


    if os.path.isfile(CelebA_ds_tensor_path):
        #if the file exists, load the tensor of the datasets
        print("The database is already loaded")
        CelebA = MyDataset(utils.load_tensor(CelebA_ds_tensor_path))
        print("Number of tensors: ", len(CelebA.samples))
    else:
        print("The database is not loaded yet")
        CelebA = load_dataset(178, 218, nb_samples=40000, crop_images=True)
        print("Number of tensors: ", len(CelebA.samples))
        utils.save_tensor_to_disk_numpy(CelebA.samples, CelebA_ds_tensor_path)
    print("This is the shape of the tensors in CelebA: ", CelebA.samples[0].shape)

    print(type(CelebA))


    p_train = 0.8
    p_valid = 0.1

    train_ds, valid_ds, test_ds = split_train_valid_test_set(CelebA, p_train, p_valid)


    ############################## Loading the dataset into a DataLoader ###################
    my_batch_size = 10

    """
    #Full dataloader
    CelebA_dl = DataLoader(CelebA, batch_size=my_batch_size, shuffle=True)
    print(f"Full dataset contains : {len(CelebA)} images")
    print(f"Full dataloader contains : {len(CelebA_dl)} batchs each containing {my_batch_size} images \n")
    """
    # DataLoader d'entrainement
    train_dl = DataLoader(train_ds, batch_size=my_batch_size, shuffle=True)
    print(f"Training dataset contains : {len(train_ds)} images")
    print(f"Training dataloader contains : {len(train_dl)} batchs each containing {my_batch_size} images \n")

    # DataLoader de validation
    valid_dl = DataLoader(valid_ds, batch_size=my_batch_size)
    print(f"Validation dataset contains: {len(valid_ds)} images")
    print(f"Validation dataloader contains : {len(valid_dl)} batchs each containing {my_batch_size} images")

    for batch_idx, batch in enumerate(train_dl):
        print(f"Batch {batch_idx} shape: {batch.shape}")
        break  # Only print the first batch

    ###################### Showing some images from the CelebA dataset constructed#############
    print("This is are images obtained from tensors in the CelebA dataset:")
    plot_5_images(CelebA, 160, 160)

    ##Architecture Summary
    width = 160
    height = 160
    nb_chan_out = 64
    AutoEncoder = Autoencoder()  # width, height, nb_chan_out)
    print("AutoEncoder model:")
    print(summary(AutoEncoder, (3, width, height)))

    # Before actually training the model check if there is a trained model already
    model = Autoencoder()
    model_path = os.path.join(utils.get_path(env_path, "Encoder"), "model40k.pt")
    print(model_path)
    """
    # Check if the model file exists
    if os.path.isfile(model_path):
        # If the file exists, load the saved weights
        print("Model is already trained")
        model = Autoencoder()
        model.load_state_dict(torch.load(model_path))

    else:
        model = Autoencoder()
        model = train_autoencoder(model, train_dl, nb_epochs=20, learning_rate=0.001)
        # Save Model
        torch.save(model.state_dict(), model_path)
    """
    ################################## Training the Autoencoder
    model = test_train_model(model, train_dl, valid_dl, nb_epochs = 100, learning_rate = 0.001)
    torch.save(model.state_dict(), model_path)

    ################################ Save some decoded images
    for i, image in enumerate(CelebA[:5]):
        decoded = encode_decode_tensor(image)
        transform = T.ToPILImage()
        img = transform(decoded)
        img.save(os.path.join(utils.get_path(env_path, "Encoder"),"gen_img",f'img{i}.jpg'))
