import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

'''
Task:
Inputs a series of data and then echoes it after a few time-steps
'''

# necessary parameters
num_epochs = 100
total_series_length = 50000
truncated_backprop_length = 15 #truncated BPTT
state_size = 4
num_classes = 2
echo_step = 3
batch_size = 5
num_batches = total_series_length//batch_size//truncated_backprop_length

# Generating a random series of data for input
def generateData():
    x = np.array(np.random.choice(2, total_series_length, p=[0.5, 0.5])) # Generating a vector of binary constant with lenght of series
    y = np.roll(x, echo_step) # Shift by echo_step steps of x to get y
    y[0:echo_step] = 0

    # reshaping of the data into a matrix with batch_size rows
    x = x.reshape((batch_size, -1))  # The first index changing slowest, subseries as rows
    y = y.reshape((batch_size, -1))

    return (x, y)

# Visualizing the training
def plot(loss_list, predictions_series, batchX, batchY):
    plt.subplot(2, 3, 1)
    plt.cla()
    plt.plot(loss_list)

    for batch_series_idx in range(5):
        one_hot_output_series = np.array(predictions_series)[:, batch_series_idx, :]
        single_output_series = np.array([(1 if out[0] < 0.5 else 0) for out in one_hot_output_series])

        plt.subplot(2, 3, batch_series_idx + 2)
        plt.cla()
        plt.axis([0, truncated_backprop_length, 0, 2])
        left_offset = range(truncated_backprop_length)
        plt.bar(left_offset, batchX[batch_series_idx, :], width=1, color="blue")
        plt.bar(left_offset, batchY[batch_series_idx, :] * 0.5, width=1, color="red")
        plt.bar(left_offset, single_output_series * 0.3, width=1, color="green")

    plt.draw()
    plt.pause(0.0001)


# Starting nodes of the computational graph
# RNN will simultaneously be training on different parts in the time-series
batchX_placeholder = tf.placeholder(tf.float32, [batch_size, truncated_backprop_length])
batchY_placeholder = tf.placeholder(tf.int32, [batch_size, truncated_backprop_length])

# Stores simultaneously training states
init_state = tf.placeholder(tf.float32, [batch_size, state_size])

# Weights and biases, they could be updated across runs
W = tf.Variable(np.random.rand(state_size+1, state_size), dtype=tf.float32)
b = tf.Variable(np.zeros((1,state_size)), dtype=tf.float32)

W2 = tf.Variable(np.random.rand(state_size, num_classes),dtype=tf.float32)
b2 = tf.Variable(np.zeros((1,num_classes)), dtype=tf.float32)

# Unpack columns (unpacking the columns of the batch into a Python list)
# unpack change to unstack
inputs_series = tf.unstack(batchX_placeholder, axis=1)
labels_series = tf.unstack(batchY_placeholder, axis=1)

# Forward pass
current_state = init_state
states_series = []
for current_input in inputs_series:
    current_input = tf.reshape(current_input, [batch_size, 1])

    # Change the parameters for tf.concat
    input_and_state_concatenated = tf.concat([current_input, current_state], 1)  # Increasing number of columns

    # current_input * Wa + current_state * Wb + b
    next_state = tf.tanh(tf.matmul(input_and_state_concatenated, W) + b)  # Broadcasted addition
    states_series.append(next_state)
    current_state = next_state

# Calculating loss
logits_series = [tf.matmul(state, W2) + b2 for state in states_series] #Broadcasted addition

# softmax layer from the state to the output (one-hot vector)
predictions_series = [tf.nn.softmax(logits) for logits in logits_series]

# sparse_softmax_cross_entropy_with_logits calculates the softmax and the cross-entropy
# changed function parameters
losses = [tf.nn.sparse_softmax_cross_entropy_with_logits(logits=logits, labels=labels) for logits, labels in zip(logits_series,labels_series)]
total_loss = tf.reduce_mean(losses)

# Adagrad algorithm to train
train_step = tf.train.AdagradOptimizer(0.3).minimize(total_loss)

# Training session
with tf.Session() as sess:
    sess.run(tf.initialize_all_variables())
    plt.ion()
    plt.figure()
    plt.show()
    loss_list = []

    for epoch_idx in range(num_epochs):
        x,y = generateData()
        _current_state = np.zeros((batch_size, state_size))

        print("New data, epoch", epoch_idx)

        for batch_idx in range(num_batches):
            start_idx = batch_idx * truncated_backprop_length
            end_idx = start_idx + truncated_backprop_length

            # Slice the input data and label
            batchX = x[:,start_idx:end_idx]
            batchY = y[:,start_idx:end_idx]

            _total_loss, _train_step, _current_state, _predictions_series = sess.run(
                [total_loss, train_step, current_state, predictions_series],
                # Feed varaibles for each batch from inputting stage
                feed_dict={
                    batchX_placeholder:batchX,
                    batchY_placeholder:batchY,
                    init_state:_current_state
                })

            loss_list.append(_total_loss)

            if batch_idx%100 == 0:
                print("Step",batch_idx, "Loss", _total_loss)
                plot(loss_list, _predictions_series, batchX, batchY)

plt.ioff()
plt.show()