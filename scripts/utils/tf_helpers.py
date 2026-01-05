"""
Text-Fabric helper utilities for the TR pipeline.

Provides common operations for loading and working with Text-Fabric datasets.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


def load_n1904(config: dict) -> Any:
    """
    Load the N1904 Text-Fabric dataset.

    Args:
        config: Loaded config dict

    Returns:
        Text-Fabric API object

    Raises:
        ImportError: If text-fabric is not installed
        Exception: If dataset cannot be loaded
    """
    try:
        from tf.app import use
    except ImportError:
        raise ImportError(
            "text-fabric is not installed. Run: pip install text-fabric"
        )

    n1904_config = config["sources"]["n1904"]

    # Try local path first if specified
    local_path = n1904_config.get("local_path")
    if local_path and Path(local_path).exists():
        logger.info(f"Loading N1904 from local path: {local_path}")
        TF = use(local_path, silent="deep")
    else:
        # Load from Text-Fabric data repository
        dataset = n1904_config["tf_dataset"]
        logger.info(f"Loading N1904 from TF repository: {dataset}")
        TF = use(dataset, silent="deep")

    return TF


def get_all_otypes(api: Any) -> List[str]:
    """
    Get all node types (otypes) from a Text-Fabric API.

    Args:
        api: Text-Fabric API object

    Returns:
        List of otype names
    """
    return list(api.F.otype.freqList())


def get_features_for_otype(api: Any, otype: str) -> List[str]:
    """
    Get all features available for a given otype.

    Args:
        api: Text-Fabric API object
        otype: Node type name

    Returns:
        List of feature names that have values for this otype
    """
    features = []
    sample_nodes = list(api.F.otype.s(otype))[:10]

    if not sample_nodes:
        return features

    # Check each feature
    for feature_name in dir(api.F):
        if feature_name.startswith("_"):
            continue
        feature = getattr(api.F, feature_name, None)
        if feature is None:
            continue
        # Try to get value for sample nodes
        try:
            for node in sample_nodes:
                val = feature.v(node)
                if val is not None:
                    features.append(feature_name)
                    break
        except Exception:
            pass

    return sorted(features)


def get_edge_features(api: Any) -> List[str]:
    """
    Get all edge feature names from a Text-Fabric API.

    Args:
        api: Text-Fabric API object

    Returns:
        List of edge feature names
    """
    edge_features = []
    for name in dir(api.E):
        if not name.startswith("_"):
            edge_features.append(name)
    return sorted(edge_features)


def extract_schema(api: Any) -> Dict[str, Any]:
    """
    Extract the complete schema from a Text-Fabric dataset.

    Args:
        api: Text-Fabric API object

    Returns:
        Schema dict with otypes, features, and edge features
    """
    schema = {
        "otypes": [],
        "features": {},
        "edge_features": [],
        "otype_counts": {},
    }

    # Get otypes and their counts
    for otype, count in api.F.otype.freqList():
        schema["otypes"].append(otype)
        schema["otype_counts"][otype] = count
        schema["features"][otype] = get_features_for_otype(api, otype)

    # Get edge features
    schema["edge_features"] = get_edge_features(api)

    return schema


def get_book_names(api: Any) -> List[str]:
    """
    Get list of book names from the dataset.

    Args:
        api: Text-Fabric API object

    Returns:
        List of book names in order
    """
    books = []
    for node in api.F.otype.s("book"):
        book_name = api.T.sectionFromNode(node)[0]
        books.append(book_name)
    return books


def verse_words(api: Any, book: str, chapter: int, verse: int) -> List[Tuple[int, str]]:
    """
    Get all words in a verse with their node IDs.

    Args:
        api: Text-Fabric API object
        book: Book name
        chapter: Chapter number
        verse: Verse number

    Returns:
        List of (node_id, word_text) tuples
    """
    words = []
    verse_node = api.T.nodeFromSection((book, chapter, verse))
    if verse_node is None:
        return words

    for word_node in api.L.d(verse_node, otype="word"):
        word_text = api.T.text(word_node)
        words.append((word_node, word_text))

    return words


def get_word_features(api: Any, node: int, features: List[str]) -> Dict[str, Any]:
    """
    Get specified features for a word node.

    Args:
        api: Text-Fabric API object
        node: Word node ID
        features: List of feature names to extract

    Returns:
        Dict mapping feature names to values
    """
    result = {}
    for feature in features:
        feat_obj = getattr(api.F, feature, None)
        if feat_obj is not None:
            result[feature] = feat_obj.v(node)
    return result


def get_parent_chain(api: Any, node: int, max_depth: int = 20) -> List[int]:
    """
    Get the parent chain for a node (for detecting cycles).

    Args:
        api: Text-Fabric API object
        node: Starting node
        max_depth: Maximum depth to traverse (for cycle detection)

    Returns:
        List of parent node IDs
    """
    chain = []
    current = node
    depth = 0

    while depth < max_depth:
        parents = api.E.parent.t(current) if hasattr(api.E, "parent") else []
        if not parents:
            break
        parent = parents[0]  # Assume single parent
        if parent in chain:
            # Cycle detected
            chain.append(parent)
            break
        chain.append(parent)
        current = parent
        depth += 1

    return chain


if __name__ == "__main__":
    # Test the helpers
    from .config import load_config

    config = load_config()
    print("Loading N1904...")

    try:
        api = load_n1904(config)
        print("N1904 loaded successfully!")

        schema = extract_schema(api)
        print(f"\nOTypes: {schema['otypes']}")
        print(f"\nEdge features: {schema['edge_features']}")
        print(f"\nWord features: {schema['features'].get('word', [])[:10]}...")
    except Exception as e:
        print(f"Error: {e}")
        print("(This is expected if N1904 is not installed)")
