import time

import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers import util


def generate_embeddings(phrases, model_name='all-MiniLM-L6-v2'):
    """
    Generates sentence embeddings for a list of phrases using a specified model.

    Args:
        phrases (list of str): The list of phrases to embed.
        model_name (str): The name of the sentence-transformer model to use.

    Returns:
        torch.Tensor: A tensor containing the embeddings for the phrases.
    """
    print(f'Loading sentence transformer model: {model_name}...')
    # Instantiate the model. It will be downloaded automatically if not cached.
    # Using a GPU if available will significantly speed up this process.
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'Using device: {device}')
    model = SentenceTransformer(model_name, device=device)

    print(f'Generating embeddings for {len(phrases)} phrases. This might take a while...')
    start_time = time.time()

    # The encode method handles batching automatically for large lists.
    embeddings = model.encode(phrases, convert_to_tensor=True, show_progress_bar=True)

    end_time = time.time()
    print(f'Embeddings generated in {end_time - start_time:.2f} seconds.')

    return embeddings


def cluster_embeddings(embeddings, min_community_size=5, threshold=0.75):
    """
    Performs community detection (a form of hierarchical clustering) on the embeddings.

    This algorithm is much faster than traditional hierarchical clustering for large datasets.
    It doesn't require specifying the number of clusters beforehand.

    Args:
        embeddings (torch.Tensor): The embeddings to cluster.
        min_community_size (int): The minimum size of a cluster. Phrases not
                                  assigned to a cluster of this size will be
                                  grouped into a single miscellaneous cluster.
        threshold (float): A value between 0 and 1. Cosine similarity threshold.
                           Lower values will result in larger, more diverse clusters.
                           Higher values will result in smaller, more coherent clusters.

    Returns:
        list of list of int: A list of clusters, where each cluster is a list of
                             indices corresponding to the original phrases.
    """
    print('Starting clustering process...')
    start_time = time.time()

    # The community_detection function is a fast clustering algorithm from the library.
    clusters = util.community_detection(embeddings, min_community_size=min_community_size, threshold=threshold)

    end_time = time.time()
    print(f'Clustering completed in {end_time - start_time:.2f} seconds.')
    print(f'Found {len(clusters)} clusters.')

    return clusters


def main():
    """
    Main function to run the phrase clustering pipeline.
    """
    # In a real-world scenario, you would load your phrases from a file.
    # For example:
    # with open('my_phrases.txt', 'r') as f:
    #     phrases = [line.strip() for line in f]
    # Here, we use a sample list for demonstration.
    with open('./traits.txt', 'r') as f:
        phrases = [line.strip() for line in f if line.strip()]

    # You can scale this up to 50,000 or more phrases.
    # For a large list, the process will take longer and require more memory.
    # print(f"Processing {len(phrases)} sample phrases.")

    # Step 1: Generate embeddings for the phrases
    embeddings = generate_embeddings(phrases)

    # Step 2: Cluster the embeddings
    # Adjust min_community_size and threshold based on your dataset and desired granularity.
    # For 50k items, you might start with a higher min_community_size (e.g., 10 or 25).
    # A threshold of 0.75 is a good starting point for high similarity.
    clusters = cluster_embeddings(embeddings, min_community_size=2, threshold=0.6)

    # Step 3: Print the results
    print('\n--- Clustering Results ---')
    for i, cluster in enumerate(clusters):
        print(f'\nCluster {i + 1} ({len(cluster)} phrases):')
        for phrase_index in cluster:
            print(f'  - {phrases[phrase_index]}')


if __name__ == '__main__':
    main()
