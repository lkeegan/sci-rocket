from workflow.scripts.demultiplexing.demux_gather import combine_pickle


def test_combine_pickle_keeps_max_r2_read_length():
    combined = {
        "experiment_name": "exp",
        "version": "0.0.0",
        "max_r2_read_length": 84,
    }
    incoming = {
        "experiment_name": "exp",
        "version": "0.0.0",
        "max_r2_read_length": 101,
    }

    merged = combine_pickle(incoming, combined)
    assert merged["max_r2_read_length"] == 101

    incoming_smaller = {
        "experiment_name": "exp",
        "version": "0.0.0",
        "max_r2_read_length": 90,
    }
    merged = combine_pickle(incoming_smaller, merged)
    assert merged["max_r2_read_length"] == 101


def test_combine_pickle_sets_max_r2_read_length_if_missing():
    combined = {
        "experiment_name": "exp",
        "version": "0.0.0",
    }
    incoming = {
        "experiment_name": "exp",
        "version": "0.0.0",
        "max_r2_read_length": 92,
    }

    merged = combine_pickle(incoming, combined)
    assert merged["max_r2_read_length"] == 92
