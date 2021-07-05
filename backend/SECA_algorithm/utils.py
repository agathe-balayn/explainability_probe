from sklearn.metrics import confusion_matrix
from skimage import io, transform
from scipy.io import loadmat
from tqdm import tqdm
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from . import config as cfg
import pandas as pd
import numpy as np
import itertools
import json
import os


def read_PA100K():
    """
    Return dataframe with PA-100K label data.

    Returns:
        labels: pd.Dataframe that contains the concatenated labels of train/val/test with their attribute names
    """
    data = loadmat(cfg.PA100K_LABELS)
    attribute_names = [attribute[0][0] for attribute in data["attributes"]]
    labels_train = pd.DataFrame(data=data["train_label"], columns=attribute_names)
    labels_val = pd.DataFrame(data=data["val_label"], columns=attribute_names)
    labels_test = pd.DataFrame(data=data["test_label"], columns=attribute_names)
    return labels_train, labels_val, labels_test


def read_PETA():
    """
    Return dataframe with PETA label data.

    Returns:
        labels: pd.Dataframe that contains the labels with their attribute names
    """
    if os.path.isfile("./analysis/PETA_labels.csv"):
        labels = pd.read_csv("./analysis/PETA_labels.csv", dtype={"PedestrianID": str})
    else:
        directories = [os.path.normpath(x[0]) for x in os.walk(cfg.PETA_DIRS) if "archive" in x[0]]  # keep all sub-paths that contain /archive
        paths = [os.path.join(s, "Label.txt") for s in directories]
        annotations = []
        attribute_names = set()  # unique attribute names in dataset
        # For every file, store the annotations and the unique attributes
        for path in paths:
            f = open(path, "r")
            for line in f:
                annotations.append(line)
                for attribute in line.split()[1:]:  # omit user ID
                    attribute_names.add(attribute)

        attribute_names.add("PedestrianID")
        attributes_temp = np.zeros(shape=(len(annotations), len(attribute_names)), dtype=np.int8)
        # Initializing dataframe with zeros
        labels = pd.DataFrame(data=attributes_temp, columns=sorted(attribute_names))
        annotation_count = 0
        for annotation in tqdm(annotations):
            first = True
            for attribute in annotation.split():
                if first:
                    labels.loc[annotation_count, "PedestrianID"] = str(attribute)
                    first = False
                else:
                    labels.loc[annotation_count, attribute] = int(1)
            annotation_count += 1
        labels.to_csv("./analysis/PETA_labels.csv", index=False)
    return labels


def plot_stacked_bar_chart(title, feature_counts, legend_text):
    """
    Plot attribute count bar chart.

    Args:
        title (string): stacked bar chart title
        feature_counts (pd.Dataframe): Pandas Dataframe that contains the counts of each attribute value
        legend_text (tuple): tuple of strings corresponding to the class names
    """
    feat_count = len(feature_counts.columns)
    ind = np.arange(feat_count)  # the x locations for the groups
    width = 0.35  # the width of the bars: can also be len(x) sequence
    p1 = plt.bar(ind, feature_counts.values[0], width)  # plot attributes with 0
    p2 = plt.bar(ind, feature_counts.values[1], width, bottom=feature_counts.values[0])
    plt.ylabel("Counts")
    plt.title(title)
    plt.xticks(ind, feature_counts.columns, rotation="vertical")
    plt.legend((p1[0], p2[0]), legend_text, loc="upper right")


def save_pa100_labels():
    """
    Save train/val/test .npy files with gender/sleeve/ortientation labels in the data folder.
    """
    if not os.path.isfile(cfg.PA100K_LABEL_TRAIN_PATH):
        pa100k_train, pa100k_val, pa100k_test = read_PA100K()
        # Mapping to new attributes
        train_labels = label_mapping(pa100k_train)
        val_labels = label_mapping(pa100k_val)
        test_labels = label_mapping(pa100k_test)
        # Saving labels to .npy
        np.save(cfg.PA100K_LABEL_TRAIN_PATH, train_labels)
        np.save(cfg.PA100K_LABEL_VAL_PATH, val_labels)
        np.save(cfg.PA100K_LABEL_TEST_PATH, test_labels)


def label_mapping(original_labels):
    """
    Maps labels from the original dataset attributes to gender/sleeve/orientation.

    Args:
        original_labels (pd.Dataframe): Pandas Dataframe with the original dataset attributes
    Returns:
        np_labels: nd.array with the mapped attributes
    """
    # Initializing label numpy array
    np_labels = np.zeros((original_labels.shape[0], 3), dtype=int)  # x3 refers to gender/sleeve/orientation
    for index, row in tqdm(original_labels.iterrows()):
        # Gender classification - Male: 0, Female: 1
        if row["Female"] == 1:
            np_labels[index, 0] = 1
        else:
            np_labels[index, 0] = 0
        # Sleeve classification - LongSleeve: 0, ShortSleeve: 1
        if row["LongSleeve"] == 1:
            np_labels[index, 1] = 0
        elif row["ShortSleeve"] == 1:
            np_labels[index, 1] = 1
        # Orientation classification - Back: 1, Front: 2, Side: 3
        if row["Back"] == 1:
            np_labels[index, 2] = 1
        elif row["Front"] == 1:
            np_labels[index, 2] = 2
        elif row["Side"] == 1:
            np_labels[index, 2] = 3
    return np_labels


def images_to_npy(images_path):
    """
    Save train/val/test .npy files containing the RGB values of each image.

    Args:
        images_path (str): path to the folder that contains the dataset image files.
    """
    image_list = sorted(os.listdir(images_path))  # Sort images according to their name to match labels
    train_images = []
    val_images = []
    test_images = []
    # For each dataset image
    for count in tqdm(range(len(image_list))):
        image_rgb_array = io.imread(os.path.join(images_path, image_list[count]))
        if count < 80000:
            train_images.append(image_rgb_array)
        elif count < 90000:
            val_images.append(image_rgb_array)
        elif count < 100000:
            test_images.append(image_rgb_array)
    # Save data to .npy files
    np.save(cfg.PA100K_DATA_TRAIN_PATH, train_images)
    np.save(cfg.PA100K_DATA_VAL_PATH, val_images)
    np.save(cfg.PA100K_DATA_TEST_PATH, test_images)


def resize_PA100K_image(image):
    """
        Resize image to 75x75px.

        Args:
            image (numpy.ndarray): PA100K image than needs to be resized

        Return:
            resized_image (numpy.ndarray): RGB values of resized image
    """
    # Select images with 75px width or more.
    # Images with width higher than 75px, are resized to 75px width while maintaining aspect ratio
    if image.shape[1] > 75:
        resize_ratio = 75 / image.shape[1]
        image = transform.resize(image, (np.rint(image.shape[0] * resize_ratio), np.rint(image.shape[1] * resize_ratio)))
        # Convert back to int values (resize convert them to [0,1])
        image = image * 255
        image = image.astype(np.uint8)
    # Take 75 top pixels of the image height to convert it to 75x75px
    resized_image = image[0:75, :]
    return resized_image


def prepare_images(images_path):
    """
        Resize PA-100K images to 75x75 and save them to a new directory layout suitable for an ImageDataGenerator:
            - data
                - train
                    - male
                    - female
                - validation
                    - male
                    - female
                - test
                    - male
                    - female

        Args:
            images_path (str): path to original PA-100K images
    """
    image_list = sorted(os.listdir(images_path))
    # Read labels
    mat_file = loadmat(cfg.PA100K_LABELS)
    attribute_names = [attribute[0][0] for attribute in mat_file["attributes"]]
    labels_train = label_mapping(pd.DataFrame(data=mat_file["train_label"], columns=attribute_names))
    labels_train = labels_train[:, [0]]  # selecting gender labels
    labels_val = label_mapping(pd.DataFrame(data=mat_file["val_label"], columns=attribute_names))
    labels_val = labels_val[:, [0]]  # selecting gender labels
    labels_test = label_mapping(pd.DataFrame(data=mat_file["test_label"], columns=attribute_names))
    labels_test = labels_test[:, [0]]  # selecting gender labels
    # For each dataset image
    for count in tqdm(range(len(image_list))):
        image_rgb_array = io.imread(os.path.join(images_path, image_list[count]))
        # Ignore images with width less than 75. TODO: I can also try upsampling and keeping them
        if image_rgb_array.shape[1] < 75:
            continue
        resized_image_rgd_array = resize_PA100K_image(image_rgb_array)
        if count < 80000:
            if labels_train[count] == 0:
                io.imsave(os.path.join(cfg.DATA_TRAIN, "male/", image_list[count]), resized_image_rgd_array)
            else:
                io.imsave(os.path.join(cfg.DATA_TRAIN, "female/", image_list[count]), resized_image_rgd_array)
        elif count < 90000:
            if labels_val[count - 80000] == 0:
                io.imsave(os.path.join(cfg.DATA_VAL, "male/", image_list[count]), resized_image_rgd_array)
            else:
                io.imsave(os.path.join(cfg.DATA_VAL, "female/", image_list[count]), resized_image_rgd_array)
        elif count < 100000:
            if labels_test[count - 90000] == 0:
                io.imsave(os.path.join(cfg.DATA_TEST, "male/", image_list[count]), resized_image_rgd_array)
            else:
                io.imsave(os.path.join(cfg.DATA_TEST, "female/", image_list[count]), resized_image_rgd_array)


def visualize_predictions(y_pred, y_true, test_generator):
    """
        Visualize 15 random images from the test set, coupled with their true and predicted labels.

        Args:
            y_pred (nd.array): labels predicted by the trained model
            y_true (nd.array): true labels of the samples
            test_generator (ImageDataGenerator): contains the indexes/names of the images used for prediction
    """
    # Get the class encoding used by the data generator
    label_values = test_generator.class_indices
    label_values = dict((v, k) for k, v in label_values.items())
    # Select 15 random images
    random_image_selection = np.random.choice(len(test_generator.filenames), 15)
    selected_images = np.array(test_generator.filenames)[random_image_selection]
    # Show selected images with true/predicted labels
    fig = plt.figure(figsize=(20, 20))
    for i, img in enumerate(selected_images):
        fig.add_subplot(3, 5, i + 1)
        plt.title("True: " + label_values[y_true[random_image_selection[i]]] + " Predicted: " +
                  label_values[y_pred[random_image_selection[i]]])
        plt.imshow(io.imread(os.path.join(cfg.DATA_TEST, img)))
    plt.show()


def compute_accuracy(y_pred, y_true):
    """
        Compute model accuracy on the test set.

        Args:
            y_pred (nd.array): labels predicted by the trained model
            y_true (nd.array): true labels of the samples
    """
    # Compute accuracy
    correct_predictions = 0
    for i in range(len(y_true)):
        if y_pred[i] == y_true[i]:
            correct_predictions += 1
    accuracy = correct_predictions / len(y_true)
    print("\nCustom Test accuracy:", np.round(accuracy * 100, 2))


def plot_confusion_matrix(y_pred, y_true, classes, normalize=False):
    """
        Plot confusion matrix of the true/predicted labels.

        Args:
            y_pred (nd.array): labels predicted by the trained model
            y_true (nd.array): true labels of the samples
            classes (list): list containing the string names of each label
            normalize (bool): option to print percentages instead of count values
    """
    cm = confusion_matrix(y_true, y_pred)
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes)
    plt.yticks(tick_marks, classes)
    if normalize:
        cm = np.round(cm.astype("float") / cm.sum(axis=1)[:, np.newaxis], 2)  # compute percentages
        plt.title("Normalized Confusion Matrix")
    else:
        plt.title("Confusion Matrix")
    plt.imshow(cm, cmap=plt.get_cmap("Blues"))
    plt.colorbar()
    thresh = cm.max() / 2.
    # Plot the TP, TN, FP, FN on the figure
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, cm[i, j], horizontalalignment="center", verticalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
    plt.tight_layout()
    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.show()


def show_image(image_rgb, title="", ax=None):
    """
        Shows specified image.

        Args:
            image_rgb (nd.array): path to specific image in the dataset
            title (str): figure title
            ax (plt.subplot): position of the subplot
    """
    image = np.squeeze(image_rgb)  # remove extra tensor dimension
    image = image / 127.5 - 1.0
    if ax is None:
        plt.figure()
    plt.axis("off")
    image = ((image + 1) * 127.5).astype(np.uint8)
    plt.imshow(image)
    plt.title(title)


def load_image(image_path):
    """
        Loads specified image.

        Args:
            image_path (str): path to specific image in the dataset
    """
    image = io.imread(image_path)
    return image


def show_grayscale_image(saliency_map, title="", ax=None):
    """
        Shows extracted saliency map in grayscale format.

        Args:
            saliency_map (nd.array): extracted saliency map
            title (str): figure title
            ax (plt.subplot): position of the subplot
    """
    if ax is None:
        plt.figure()
    plt.axis("off")

    plt.imshow(saliency_map, cmap=plt.cm.gray, vmin=0, vmax=1)
    plt.title(title)


def show_heat_map(saliency_map, title="", ax=None):
    """
        Shows heatmap of extracted saliency map.

        Args:
            saliency_map (nd.array): extracted saliency map
            title (str): figure title
            ax (plt.subplot): position of the subplot
    """
    if ax is None:
        plt.figure()
    plt.axis("off")
    plt.imshow(saliency_map, cmap="inferno")
    plt.title(title)


def plot_image_saliency_maps(image, vanilla_mask, smoothgrad_mask, total_rows, rendered_figs, first_image):
    """
        Plots the following graphs for the provided image.

        Args:
            image (nd.array): image RGB values
            vanilla_mask (nd.array): extracted gradient mask
            smoothgrad_mask (nd.array): extracted smoothgrad map
            total_rows (int): number of images
            rendered_figs (int): number of figures that have already been rendered
            first_image (bool): used to turn the figure titles off
    """
    # Compute most salient 30% of the image
    mask = smoothgrad_mask > np.percentile(smoothgrad_mask, 70)
    im_mask = np.array(image)
    im_mask[~mask] = 0
    # Render the saliency masks
    if first_image:
        show_image(image, title="Original Image", ax=plt.subplot(total_rows, 5, rendered_figs + 1))
        show_grayscale_image(vanilla_mask, title="Vanilla Gradient", ax=plt.subplot(total_rows, 5, rendered_figs + 2))
        show_grayscale_image(smoothgrad_mask, title="SmoothGrad", ax=plt.subplot(total_rows, 5, rendered_figs + 3))
        show_heat_map(smoothgrad_mask, title="SmoothGrad Heatmap", ax=plt.subplot(total_rows, 5, rendered_figs + 4))
        show_image(im_mask, title="Top 30%", ax=plt.subplot(total_rows, 5, rendered_figs + 5))
    else:
        show_image(image, title="", ax=plt.subplot(total_rows, 5, rendered_figs + 1))
        show_grayscale_image(vanilla_mask, title="", ax=plt.subplot(total_rows, 5, rendered_figs + 2))
        show_grayscale_image(smoothgrad_mask, title="", ax=plt.subplot(total_rows, 5, rendered_figs + 3))
        show_heat_map(smoothgrad_mask, title="", ax=plt.subplot(total_rows, 5, rendered_figs + 4))
        show_image(im_mask, title="", ax=plt.subplot(total_rows, 5, rendered_figs + 5))


def visualize_crowd_annotations(heatmap_annotations, heatmap_name, heatmap):
    """
        Plots the bounding box annotations for a specific heatmap image.

        Args:
            heatmap_annotations (pd.DataFrame): annotations for specific image
            heatmap_name (str): name of the heatmap image
            heatmap (nd.array): heatmap image RGB values
    """
    fig, axs = plt.subplots(1, 5)
    fig.suptitle("Heatmap name: " + heatmap_name)
    # Plot original heatmap without annotaitons
    axs[0].imshow(heatmap)
    axs[0].set_title("Raw heatmap")
    axs[0].axis("off")
    for index, annotation in enumerate(heatmap_annotations["Answer.annotation_data"]):
        updated_index = index + 1  # to account for the original heatmap
        col = updated_index if updated_index < 6 else updated_index - 6  # subplot column
        json_annotation = json.loads(annotation)
        # Plot image and worker ID
        axs[col].imshow(heatmap)
        axs[col].set_title(heatmap_annotations.iloc[index, 1])
        axs[col].axis("off")
        # For each bounding box/description
        for bounding_box in json_annotation:
            # Plot bounding box
            box = patches.Rectangle((bounding_box["left"], bounding_box["top"]), bounding_box["width"], bounding_box["height"], linewidth=2, edgecolor="g",
                                    facecolor="none")
            axs[col].add_patch(box)
            # Plot description
            element_description = bounding_box["object_label"] + ": \n" + bounding_box["attributes_label"]
            axs[col].annotate(element_description, (bounding_box["left"] + 2, bounding_box["top"] + 2), color="g", fontsize=12, ha="left", va="top")
    # Maximize plot window
    fig_manager = plt.get_current_fig_manager()
    fig_manager.window.showMaximized()
    plt.show()
    fig.savefig(os.path.join("path_crowd_computing_output", heatmap_name[:-4] + ".png"))


def intersection(list_1, list_2):
    """
        Compute the intersection list between two string lists.
        Args:
            list_1 (list): first list of intersection
            list_2 (list): second list of intersection
        Return:
            intersection_list (list): intersection of list_1 and list_2
    """
    intersection_list = [value for value in list_1 if value in list_2]
    return intersection_list


def union(list_1, list_2):
    """
        Compute the union list between two string lists.
        Args:
            list_1 (list): first list of union
            list_2 (list): second list of union
        Return:
            union_list (list): union of list_1 and list_2
    """
    union_list = list(set(list_1 + list_2))
    return union_list


def jaccard_similarity(list_1, list_2):
    """
        Compute the Jaccard similarity value for two string lists.
        Args:
            list_1 (list): first list
            list_2 (list): second list
        Return:
            jaccard_value (float): Jaccard similarity value
    """
    intersection_length = len(intersection(list_1, list_2))
    union_length = len(union(list_1, list_2))
    jaccard_value = intersection_length / union_length
    return jaccard_value


def precision(predicted_features, ground_truth):
    """
        Compute the precision value for a list of predicted features versus the ground truth.
        Args:
            predicted_features (list): predicted semantic features
            ground_truth (list): ground truth semantic features
        Return:
            precision_value (float): precision value
    """
    if len(predicted_features) == 0:
        precision_value = 0.0
    else:
        intersection_length = len(intersection(predicted_features, ground_truth))
        precision_value = intersection_length / len(predicted_features)
    return precision_value


def recall(predicted_features, ground_truth):
    """
        Compute the recall value for a list of predicted features versus the ground truth.
        Args:
            predicted_features (list): predicted semantic features
            ground_truth (list): ground truth semantic features
        Return:
            recall_value (float): recall value
    """
    intersection_length = len(intersection(predicted_features, ground_truth))
    recall_value = intersection_length / len(ground_truth)
    return recall_value


def compute_MAE(predicted_features, ground_truth):
    """
        Compute the MAE value for a dict of predicted features versus the ground truth.
        Args:
            predicted_features (dict): predicted semantic features with their cramer values
            ground_truth (dict): ground truth semantic features with their cramer values
        Return:
            mae_value (float): MAE value
    """
    ground_truth_features = ground_truth.keys()
    mae_value = 0
    num_of_elements = 0
    for extracted_feature in predicted_features.keys():
        if extracted_feature in ground_truth_features:
            mae_value += np.absolute(ground_truth[extracted_feature] - predicted_features[extracted_feature])
            num_of_elements += 1
    if num_of_elements == 0:
        mae_value = np.nan
    else:
        mae_value = mae_value / num_of_elements  # normalize by number of extracted features
    return mae_value


def extract_evaluation_metrics(extracted_feature_lists, annotation_sizes, cramers_filter, filter_type):
    """
        Computes the precision, recall and jaccard similarity evaluation metrics for the semantic features extracted.
        Args:
            extracted_feature_lists (dict): json object containing the ground truth and extracted lists
            annotation_sizes (range): range of annotation sizes to be tried out
            cramers_filter (float): cramer value that should be used to filter semantic features
            filter_type (str): specifies the filter type to be used (higher, lower, bin)
        Return:
            experiment_metrics_df (pd.Dataframe): metrics dataframe contain the avg computed metrics with their std per annotation size
    """
    # Initialize metric values
    jaccard_values = np.zeros((len(annotation_sizes), len(extracted_feature_lists['iterations'])))
    recall_values = np.zeros((len(annotation_sizes), len(extracted_feature_lists['iterations'])))
    precision_values = np.zeros((len(annotation_sizes), len(extracted_feature_lists['iterations'])))
    mae_values = np.zeros((len(annotation_sizes), len(extracted_feature_lists['iterations'])))
    wrong_features_02_count = np.zeros((len(annotation_sizes), len(extracted_feature_lists['iterations'])))
    wrong_features_04_count = np.zeros((len(annotation_sizes), len(extracted_feature_lists['iterations'])))
    wrong_features_1_count = np.zeros((len(annotation_sizes), len(extracted_feature_lists['iterations'])))
    if filter_type == 'higher':
        feature_filter = lambda feature_dict: {k: v for k, v in feature_dict.items() if v >= cramers_filter}
    elif filter_type == 'lower':
        feature_filter = lambda feature_dict: {k: v for k, v in feature_dict.items() if v <= cramers_filter}
    elif filter_type == 'bin':
        feature_filter = lambda feature_dict: {k: v for k, v in feature_dict.items() if cramers_filter - 0.2 < v <= cramers_filter}
    for iteration, iteration_lists in enumerate(extracted_feature_lists['iterations']):
        iteration_ground_truth = feature_filter(iteration_lists['ground_truth'])
        # If ground truth is not empty
        if bool(iteration_ground_truth):
            for size_idx, annotation_size in enumerate(iteration_lists['extracted_lists']):
                extracted_semantic_features = feature_filter(iteration_lists['extracted_lists'][annotation_size])
                features_not_in_ground_truth = {feature: iteration_lists['extracted_lists'][annotation_size][feature] for feature in
                                                iteration_lists['extracted_lists'][annotation_size].keys() if feature not in iteration_ground_truth.keys()}
                wrong_feaures_02 = {k: v for k, v in features_not_in_ground_truth.items() if 0 < v <= 0.2}
                wrong_feaures_04 = {k: v for k, v in features_not_in_ground_truth.items() if 0.2 < v <= 0.4}
                wrong_feaures_1 = {k: v for k, v in features_not_in_ground_truth.items() if v > 0.4}
                wrong_features_02_count[size_idx][iteration] = len(wrong_feaures_02)
                wrong_features_04_count[size_idx][iteration] = len(wrong_feaures_04)
                wrong_features_1_count[size_idx][iteration] = len(wrong_feaures_1)
                jaccard_values[size_idx][iteration] = jaccard_similarity(list(extracted_semantic_features), list(iteration_ground_truth))
                precision_values[size_idx][iteration] = precision(list(iteration_lists['extracted_lists'][annotation_size]), list(iteration_ground_truth))
                recall_values[size_idx][iteration] = recall(list(iteration_lists['extracted_lists'][annotation_size]), list(iteration_ground_truth))
                mae_values[size_idx][iteration] = compute_MAE(iteration_lists['extracted_lists'][annotation_size], iteration_ground_truth)
    # Compute average values over x runs
    jaccard_mean = np.mean(jaccard_values, axis=1)
    jaccard_std = np.std(jaccard_values, axis=1)
    precision_mean = np.mean(precision_values, axis=1)
    precision_std = np.std(precision_values, axis=1)
    recall_mean = np.mean(recall_values, axis=1)
    recall_std = np.std(recall_values, axis=1)
    mae_mean = np.nanmean(mae_values, axis=1)
    mae_std = np.nanstd(mae_values, axis=1)
    wrong_features_02_mean = np.mean(wrong_features_02_count, axis=1)
    wrong_features_02__std = np.std(wrong_features_02_count, axis=1)
    wrong_features_04_mean = np.mean(wrong_features_04_count, axis=1)
    wrong_features_04_std = np.std(wrong_features_04_count, axis=1)
    wrong_features_1_mean = np.mean(wrong_features_1_count, axis=1)
    wrong_features_1_std = np.std(wrong_features_1_count, axis=1)
    experiment_metrics_df = pd.DataFrame(
        columns=['annotation_size', 'jaccard_similarity_mean', 'jaccard_similarity_std', 'precision_mean', 'precision_std', 'recall_mean', 'recall_std', 'mae_mean', 'mae_std'])
    for i, annotation_size in enumerate(annotation_sizes):
        experiment_metrics_df = experiment_metrics_df.append({'annotation_size': str(annotation_size), 'jaccard_similarity_mean': np.round(jaccard_mean[i], 3),
                                                              'jaccard_similarity_std': np.round(jaccard_std[i], 3), 'precision_mean': np.round(precision_mean[i], 3),
                                                              'precision_std': np.round(precision_std[i], 3), 'recall_mean': np.round(recall_mean[i], 3),
                                                              'recall_std': np.round(recall_std[i], 3), 'mae_mean': np.round(mae_mean[i], 3),
                                                              'mae_std': np.round(mae_std[i], 3), 'wrong_features_02_mean': np.round(wrong_features_02_mean[i], 3),
                                                              'wrong_features_02__std': np.round(wrong_features_02__std[i], 3),
                                                              'wrong_features_04_mean': np.round(wrong_features_04_mean[i], 3),
                                                              'wrong_features_04_std': np.round(wrong_features_04_std[i], 3),
                                                              'wrong_features_1_mean': np.round(wrong_features_1_mean[i], 3),
                                                              'wrong_features_1_std': np.round(wrong_features_1_std[i], 3)}, ignore_index=True)
    return experiment_metrics_df


def export_num_of_images_plots(dataset_name, dataset_salient_features, annotation_sizes, plot):
    """
        Plot the precision, recall jaccard similarity plots needed to evaluate the number of annotations that SEFA needs.
        The exported plots are saved at ./experiment_results/num_of_images/figures/
        Args:
            dataset_name (str): name of the dataset that is processed
            dataset_salient_features (dict): json object containing the ground truth and extracted lists
            annotation_sizes (range): range of annotation sizes to be tried out
            plot (str): defines which plot should be saves - precision, recall, jaccard or all
    """
    # Extract metrics
    dataset_metrics_no_filter = extract_evaluation_metrics(dataset_salient_features, annotation_sizes, cramers_filter=0, filter_type='higher')
    dataset_metrics_02 = extract_evaluation_metrics(dataset_salient_features, annotation_sizes, cramers_filter=0.2, filter_type='bin')
    dataset_metrics_04 = extract_evaluation_metrics(dataset_salient_features, annotation_sizes, cramers_filter=0.4, filter_type='bin')
    dataset_metrics_06 = extract_evaluation_metrics(dataset_salient_features, annotation_sizes, cramers_filter=0.6, filter_type='bin')
    dataset_metrics_08 = extract_evaluation_metrics(dataset_salient_features, annotation_sizes, cramers_filter=0.8, filter_type='bin')
    dataset_metrics_1 = extract_evaluation_metrics(dataset_salient_features, annotation_sizes, cramers_filter=1, filter_type='bin')
    desired_ticks = []
    # Extract ticks that are 20 annotations apart
    for idx, tick in enumerate(range(20, 410, 10)):
        if idx % 2 != 0:
            desired_ticks.append('')
        else:
            desired_ticks.append(tick)
    # Plot lines with std per dataset
    if plot == 'jaccard' or plot == 'all':
        plt.figure(figsize=(10, 8))
        plt.errorbar(dataset_metrics_no_filter['annotation_size'], dataset_metrics_no_filter['jaccard_similarity_mean'], yerr=dataset_metrics_no_filter['jaccard_similarity_std'], label=dataset_name)
        # plt.errorbar(dataset_metrics_02['annotation_size'], dataset_metrics_02['jaccard_similarity_mean'], yerr=dataset_metrics_02['jaccard_similarity_std'], ls='--', label=dataset_name + ' (0, 0.2]')
        # plt.errorbar(dataset_metrics_04['annotation_size'], dataset_metrics_04['jaccard_similarity_mean'], yerr=dataset_metrics_04['jaccard_similarity_std'], ls='--', label=dataset_name + ' (0.2, 0.4]')
        # plt.errorbar(dataset_metrics_06['annotation_size'], dataset_metrics_06['jaccard_similarity_mean'], yerr=dataset_metrics_06['jaccard_similarity_std'], ls='--', label=dataset_name + ' (0.4, 0.6]')
        # plt.errorbar(dataset_metrics_08['annotation_size'], dataset_metrics_08['jaccard_similarity_mean'], yerr=dataset_metrics_08['jaccard_similarity_std'], ls='--', label=dataset_name + ' (0.6, 0.8]')
        # plt.errorbar(dataset_metrics_1['annotation_size'], dataset_metrics_1['jaccard_similarity_mean'], yerr=dataset_metrics_1['jaccard_similarity_std'], ls='--', label=dataset_name + ' (0.8, 1]')
        plt.ylabel('Jaccard Similarity')
        plt.xlabel('Annotations')
        plt.title(dataset_name + ' - Jaccard Similarity')
        plt.ylim(ymin=-0.2, ymax=1.2)
        plt.yticks(np.arange(0, 1.2, 0.2))
        plt.grid(axis='y')
        plt.legend(loc='lower right')
        plt.savefig('./experiment_results/num_of_images/figures/' + dataset_name + '_jaccard.pdf', bbox_inches='tight')
    if plot == 'recall' or plot == 'all':
        plt.figure(figsize=(10, 8))
        plt.errorbar(dataset_metrics_no_filter['annotation_size'], dataset_metrics_no_filter['recall_mean'], yerr=dataset_metrics_no_filter['recall_std'], label=dataset_name)
        plt.errorbar(dataset_metrics_02['annotation_size'], dataset_metrics_02['recall_mean'], yerr=dataset_metrics_02['recall_std'], ls='--', label=dataset_name + ' (0, 0.2]')
        plt.errorbar(dataset_metrics_04['annotation_size'], dataset_metrics_04['recall_mean'], yerr=dataset_metrics_04['recall_std'], ls='--', label=dataset_name + ' (0.2, 0.4]')
        plt.errorbar(dataset_metrics_06['annotation_size'], dataset_metrics_06['recall_mean'], yerr=dataset_metrics_06['recall_std'], ls='--', label=dataset_name + ' (0.4, 0.6]')
        plt.errorbar(dataset_metrics_08['annotation_size'], dataset_metrics_08['recall_mean'], yerr=dataset_metrics_08['recall_std'], ls='--', label=dataset_name + ' (0.6, 0.8]')
        plt.errorbar(dataset_metrics_1['annotation_size'], dataset_metrics_1['recall_mean'], yerr=dataset_metrics_1['recall_std'], ls='--', label=dataset_name + ' (0.8, 1]')
        plt.ylabel('Recall')
        plt.xlabel('Annotations')
        plt.title(dataset_name + ' - Recall')
        locs, labels = plt.xticks()
        plt.xticks(ticks=locs, labels=desired_ticks)
        plt.ylim(ymin=-0.2, ymax=1.2)
        plt.yticks(np.arange(0, 1.2, 0.2))
        plt.grid(axis='y')
        plt.legend(loc='lower right')
        plt.savefig('./experiment_results/num_of_images/figures/' + dataset_name + '_recall.pdf', bbox_inches='tight')
    if plot == 'precision' or plot == 'all':
        plt.figure(figsize=(10, 7))
        plt.errorbar(dataset_metrics_no_filter['annotation_size'], dataset_metrics_no_filter['precision_mean'], yerr=dataset_metrics_no_filter['precision_std'], label=dataset_name)
        # plt.errorbar(dataset_metrics_02['annotation_size'], dataset_metrics_02['precision_mean'], yerr=dataset_metrics_02['precision_std'], ls='--', label=dataset_name + ' (0, 0.2]')
        # plt.errorbar(dataset_metrics_04['annotation_size'], dataset_metrics_04['precision_mean'], yerr=dataset_metrics_04['precision_std'], ls='--', label=dataset_name + ' (0.2, 0.4]')
        # plt.errorbar(dataset_metrics_06['annotation_size'], dataset_metrics_06['precision_mean'], yerr=dataset_metrics_06['precision_std'], ls='--', label=dataset_name + ' (0.4, 0.6]')
        # plt.errorbar(dataset_metrics_08['annotation_size'], dataset_metrics_08['precision_mean'], yerr=dataset_metrics_08['precision_std'], ls='--', label=dataset_name + ' (0.6, 0.8]')
        # plt.errorbar(dataset_metrics_1['annotation_size'], dataset_metrics_1['precision_mean'], yerr=dataset_metrics_1['precision_std'], ls='--', label=dataset_name + ' (0.8, 1]')
        plt.ylabel('Precision')
        plt.xlabel('Annotations')
        plt.title(dataset_name + ' - Precision')
        locs, labels = plt.xticks()
        plt.xticks(ticks=locs, labels=desired_ticks)
        plt.ylim(ymin=-0.2, ymax=1.2)
        plt.yticks(np.arange(0, 1.2, 0.2))
        plt.grid(axis='y')
        plt.legend(loc='lower right')
        plt.savefig('./experiment_results/num_of_images/figures/' + dataset_name + '_precision.pdf', bbox_inches='tight')
    if plot == 'mae' or plot == 'all':
        plt.figure(figsize=(10, 7))
        plt.errorbar(dataset_metrics_no_filter['annotation_size'], dataset_metrics_no_filter['mae_mean'], yerr=dataset_metrics_no_filter['mae_std'], label=dataset_name)
        plt.ylabel('MAE')
        plt.xlabel('Annotations')
        plt.title(dataset_name + ' - Mean Absolute Error')
        locs, labels = plt.xticks()
        plt.xticks(ticks=locs, labels=desired_ticks)
        plt.ylim(ymin=-0.05, ymax=0.3)
        plt.yticks(np.arange(0, 0.3, 0.05))
        plt.grid(axis='y')
        plt.legend(loc='lower right')
        plt.savefig('./experiment_results/num_of_images/figures/' + dataset_name + '_mae.pdf', bbox_inches='tight')
    if plot == 'wrong_features' or plot == 'all':
        plt.figure(figsize=(10, 8))
        pos_x_left = [size - 3 for size in annotation_sizes]
        pos_x_right = [size + 3 for size in annotation_sizes]
        plt.bar(pos_x_left, dataset_metrics_no_filter['wrong_features_02_mean'], width=3, label=dataset_name + ' (0, 0.2]')
        plt.bar(annotation_sizes, dataset_metrics_no_filter['wrong_features_04_mean'], width=3, label=dataset_name + ' (0.2, 0.4]')
        plt.bar(pos_x_right, dataset_metrics_no_filter['wrong_features_1_mean'], width=3, label=dataset_name + ' (0.4, 1]')
        plt.ylabel('Avg Wrong Features')
        plt.xlabel('Annotations')
        plt.xticks(annotation_sizes)
        plt.yticks(np.arange(0, 160, 10))
        plt.title(dataset_name + ' - Wrong Feature Count')
        locs, labels = plt.xticks()
        plt.xticks(ticks=locs, labels=desired_ticks)
        plt.grid(axis='y')
        plt.legend(loc='upper left')
        plt.savefig('./experiment_results/num_of_images/figures/' + dataset_name + '_wrong_features.pdf', bbox_inches='tight')
