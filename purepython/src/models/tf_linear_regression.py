import datetime

import errno
import tensorflow as tf
import numpy as np
import math
import sys

def train_softmax(x, y, x_test, y_test, learning_rate=0.005, max_iterations=1000000, regularization=1., w_diff_term_crit=0.0001, print_per_iteration=False):
    assert (x.shape[1] == x_test.shape[1],
            "train shape:" + str(x.shape) +
            " and test shape:" + str(x_test.shape) +
            " do not match in dimensionality")


    assert (x.shape[0] == y.shape[0],
            "number of training samples:" + str(x.shape) +
            " and number of labels:" + str(y.shape) +
            " do not match!")
    assert (x_test.shape[0] == y_test.shape[0],
            "number of testing samples:" + str(x_test.shape) +
            " and number of labels:" + str(y_test.shape) +
            " do not match!")


    # set up constants
    num_input_dims = x.shape[1]
    num_label_dims = y.shape[1]

    reg_fact = tf.constant(regularization, name='regularization_factor')

    with tf.name_scope('input'):
        x_input = tf.placeholder(tf.float32, shape=[None, num_input_dims], name='input')
    with tf.name_scope('target'):
        y_ = tf.placeholder(tf.float32, shape=[None, num_label_dims], name='target')

    # linear regression
    with tf.name_scope('linear_regression'):
        # init_vals = , name='truncated_normal_init_val_w')
        w = tf.Variable(tf.truncated_normal([num_input_dims, num_label_dims], stddev=1. / math.sqrt(2)), name='w')
        b = tf.Variable(tf.zeros([num_label_dims]), name='b')
        output = tf.softmax(tf.matmul(x_input, w) + b)

    with tf.name_scope('regularization'):
        l2loss = tf.nn.l2_loss(w,name="l2_loss")
        regularization_penalty = tf.reduce_sum(tf.square(l2loss), name='regularization_penalty_sum')
        regularization_penalty *= reg_fact

    with tf.name_scope('loss'):
        # squared error loss + regularizationPenalty
        loss = tf.nn.softmax_cross_entropy_with_logits(output,y_)
        # diff = y_ - output
        # sq_diff = tf.square(diff)
        # loss = tf.reduce_mean(sq_diff) + regularization_penalty
        # loss = tf.reduce_mean(sq_diff)

    with tf.name_scope('optimizer'):
        opt = tf.train.GradientDescentOptimizer(learning_rate)
        grads = opt.compute_gradients(loss)
        opt = opt.apply_gradients(grads)

    init = tf.initialize_all_variables()
    sess = tf.Session()

    sess.run(init)

    its = 0
    loss_train = -1.

    w_old = sess.run(w)[0][0]
    for i in xrange(0, max_iterations):
        w__, output__, loss__, _, regularization_penalty__ = sess.run(
            [w, output, loss, opt, regularization_penalty], feed_dict={x_input: x, y_: y})
        if i % 1 and print_per_iteration == 0:
            print "regularization_penalty:", regularization_penalty__
            print "iteration:", i
            print "weight:", w__
            print "loss:", loss__
        w_new = sess.run(w)[0][0]
        its += 1
        w_diff = np.sum(np.abs(w_new - w_old))

        # todo include termination criterion (weight change)
        if w_diff < w_diff_term_crit:
            print "reg_param:", regularization, "finished at iteration:", its, w_new
            # print "weights:", w_new
            # print "weight_difference:", w_diff
            break
        w_old = w_new

    loss_test = sess.run([loss], feed_dict={x_input: x_test, y_: y_test})
    sess.close()
    tf.reset_default_graph()
    return its, loss_test, loss_train


def train(x, y, x_test, y_test, learning_rate=0.005, max_iterations=1000000,
            regularization=1.0, w_diff_term_crit=0.001, verbose=True,
            model=None, regularization_initialization=None):

    assert (x.shape[1] == x_test.shape[1],
            "train shape:" + str(x.shape) +
            " and test shape:" + str(x_test.shape) +
            " do not match in dimensionality")
    assert (x.shape[0] == y.shape[0],
            "number of training samples:" + str(x.shape) +
            " and number of labels:" + str(y.shape) +
            " do not match!")
    assert (x_test.shape[0] == y_test.shape[0],
            "number of testing samples:" + str(x_test.shape) +
            " and number of labels:" + str(y_test.shape) +
            " do not match!")
    print "starting training lin reg", regularization, "init_reg", regularization_initialization, datetime.datetime.now()
    try:
        sys.stdout.flush()
    except IOError as e:
        if e.errno == errno.EPIPE:
            print "broken pipe?"
    # set up constants
    num_input_dims = x.shape[1]
    num_label_dims = y.shape[1]

    reg_fact = tf.constant(regularization, name='regularization_factor')

    with tf.name_scope('input'):
        x_input = tf.placeholder(tf.float32, [None, num_input_dims], name='input')
    with tf.name_scope('target'):
        y_ = tf.placeholder(tf.float32, [None, num_label_dims], name='target')

    # linear regression
    with tf.name_scope('linear_regression'):
        # linear regression
        if model == None:
            w = tf.Variable(tf.truncated_normal([num_input_dims, num_label_dims], stddev=1. / math.sqrt(2)),
                            name='w')
            # w = tf.Variable(tf.zeros([num_input_dims, num_label_dims]), name='w')
            b = tf.Variable(tf.zeros([num_label_dims]), name='b')
            # b = tf.Variable(tf.zeros([num_label_dims]), name='b')
        else:
            w = tf.Variable(model[0], name='w')
            b = tf.Variable(model[1], name='b')

        output = tf.add(tf.matmul(x_input, w), b)


    with tf.name_scope('regularization'):
        regularization_penalty = tf.reduce_sum(tf.square(w)) * reg_fact

    with tf.name_scope('loss'):
        pred_loss = output - y_
        loss_msq = tf.reduce_mean(tf.pow(pred_loss, 2))
        loss = loss_msq + regularization_penalty

    with tf.name_scope('optimizer'):
        opt = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss)

    init = tf.initialize_all_variables()
    sess = tf.Session()

    sess.run(init)

    w_old = sess.run(w)
    loss_old = sess.run([loss], feed_dict={x_input: x, y_: y})[0]

    # convergence criteria:
    # 5 consecutive error changes below threshold
    error_changes_past = [w_diff_term_crit, w_diff_term_crit, w_diff_term_crit, w_diff_term_crit,w_diff_term_crit]
    for i in xrange(0, max_iterations):

        # loss_msq__, w__, b__,output__, loss__, _, regularization_penalty__ = sess.run([loss_msq, w, b, output, loss, opt, regularization_penalty], feed_dict={x_input: x, y_: y})
        #
        # w_new = sess.run(w)
        # w_diff = np.sum(np.abs(w_new - w_old))
        # loss_diff = np.abs(loss_old - loss_new)
        # # if i % 1000 == 0:
        # #     print i, "reg", regularization, "init_reg", regularization_initialization, "w_diff:", w_diff, "loss_msq", loss_msq__, "loss", loss__, "loss_diff:", loss_diff
        # w_old = w_new
        # loss_old = loss_new
        # # if i % 1000 == 0:
        # #     t_end = datetime.datetime.now()
        # #     accuracy__ = sess.run([accuracy], feed_dict={x_input: x, y_: y})
        # #     print i,"reg", regularization, "init_reg", regularization_initialization, "accuracy:", accuracy__, "sum_red", sum_reduction__ , "reg_penalty", regularization_penalty__, "loss:", loss__, "weight_diff", w_diff
        # #     print "took:", t_end - t_start
        # #     t_start = t_end
        # #     # print "output:", output__
        # #     # print "log_output:", log_output__
        # #     # print "sum_reduction:", sum_reduction__
        # # todo include termination criterion (weight change)
        # # if w_diff < w_diff_term_crit and i != 0:
        # if loss_diff < w_diff_term_crit and i != 0:
        #     break
        w__, b__, output__, loss__, loss_msq__, _, regularization_penalty__ = sess.run(
            [w, b, output, loss, loss_msq, opt, regularization_penalty],
            feed_dict={x_input: x, y_: y})

        w_new = sess.run(w)
        w_diff = np.sum(np.abs(w_new - w_old))

        loss_new = sess.run([loss], feed_dict={x_input: x, y_: y})[0]
        loss_diff = np.abs(loss_old - loss_new)

        # if i % 100 == 0:
        #     print loss_new

        error_changes_past.append(loss_diff)
        error_changes_past.pop(0)

        loss_old = loss_new
        w_old = w_new

        if loss_diff < w_diff_term_crit:
            break
    w_old = sess.run(w)
    loss_test = sess.run([loss], feed_dict={x_input: x_test, y_: y_test})
    loss_train = sess.run([loss], feed_dict={x_input: x, y_: y})

    res_dict = {"loss": loss__, "regularization": regularization, "iterations": i, "accuracy_test": loss_test, "accuracy_train": loss_train, "model": (w__,b__)}

    if regularization_initialization != None:
        res_dict['initialized_with_regularization'] = regularization_initialization
    sess.close()
    tf.reset_default_graph()
    # TODO: rename accuracy in loss here ?
    print "finished", i, "reg", regularization, "init_reg", regularization_initialization, "accuracy_train", loss_train, "accuracy_test", loss_test, "loss", loss__, datetime.datetime.now()
    try:
        sys.stdout.flush()
    except IOError as e:
        if e.errno == errno.EPIPE:
            print "broken pipe?"
    return res_dict

def train_single_output(x, y, x_test, y_test, learning_rate=0.00001, max_iterations=1000000, regularization=1., w_diff_term_crit=0.0001, verbose=False, model=None):
    assert(x.shape[1] == x_test.shape[1],
           "train shape:" + str(x.shape) +
           " and test shape:" + str(x_test.shape) +
           " do not match in dimensionality")

    assert(x.shape[0] == y.shape[0],
           "number of training samples:" + str(x.shape) +
           " and number of labels:" + str(y.shape) +
           " do not match!")
    assert(x_test.shape[0] == y_test.shape[0],
           "number of testing samples:" + str(x_test.shape) +
           " and number of labels:" + str(y_test.shape) +
           " do not match!")

    # set up constants
    num_input_dims = x.shape[1]
    num_label_dims = y.shape[1]


    reg_fact = tf.constant(regularization, name='regularization_factor')

    with tf.name_scope('input'):
        x_input = tf.placeholder(tf.float32, [None, num_input_dims], name='input')
    with tf.name_scope('target'):
        y_ = tf.placeholder(tf.float32, [None, num_label_dims], name='target')

    # linear regression
    with tf.name_scope('linear_regression'):
        # init_vals = , name='truncated_normal_init_val_w')
        # if model == None:
        w = tf.Variable(tf.truncated_normal([num_input_dims, num_label_dims], stddev=1. / math.sqrt(2)), name='w')
        b = tf.Variable(tf.truncated_normal([num_label_dims]), name='b')
        # w = tf.Variable(np.random.randn(), name='w')
        # b = tf.Variable(np.random.randn(), name='b')

        # w = tf.Variable(model[0], name='w')
        # b = tf.Variable(model[1], name='b')
        output = tf.add(tf.mul(x_input, w), b)

    with tf.name_scope('regularization'):
        # regularization_penalty = tf.reduce_sum(w, name='regularization_penalty_sum')
        regularization_penalty = (tf.reduce_sum(tf.square(w)) * reg_fact)

    with tf.name_scope('loss'):
        # squared error loss + regularizationPenalty
        # diff = y_ - output
        # sq_diff = tf.square(diff)
        # loss = tf.reduce_mean(sq_diff) #+ regularization_penalty
        # squared error loss + regularizationPenalty
        # diff = y_ - output
        # sq_diff = tf.square(diff)
        loss = tf.reduce_mean(tf.pow(output - y_, 2)) + regularization_penalty
        # loss = tf.reduce_mean(sq_diff)

    with tf.name_scope('optimizer'):
        opt = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss)
        # grads = opt.compute_gradients(loss)
        # # g_print = tf.Print(opt, [opt], "gradient")
        #
        # opt_apply_grads = opt.apply_gradients(grads)

    init = tf.initialize_all_variables()
    sess = tf.Session()

    sess.run(init)

    its = 0
    loss_train = -1.

    w_old = sess.run(w)[0][0]
    with sess.as_default():
        for i in xrange(0,max_iterations):
            # for x__,y__ in zip(x,y):
            # print "input:", x__
            # print "outputgt:", y__
            # print "w_before:", w.eval()
            # print "b_before:", b.eval()
            _, w__, b__, o__, loss__ = sess.run([opt, w, b, output, loss], feed_dict={x_input: x, y_: y});
            # print i, "w", w__, b__, "loss:", loss__#, "ou", o__
            # print ""
            # w__, b__, output__, diff__, sq_diff__, loss__, _, regularization_penalty__ = sess.run([w, b, output, diff, sq_diff, loss, opt_apply_grads, regularization_penalty], feed_dict={x_input: x, y_: y})
            # # if i % 1 and verbose:
            # print "iteration:", i
            # print "w__", w__
            # print "b__", b__
            # # print "diff__", diff__
            # # print "sq_diff__", sq_diff__
            # print "loss__", loss__
            # print "regularization_penalty__", regularization_penalty__
            # # print "regularization_penalty:", regularization_penalty__
            # # print "iteration:", i
            # # print "weight:", w__
            # # print "loss:", loss__
            # print ""
            w_new = sess.run(w)[0][0]
            its += 1
            w_diff = np.sum(np.abs(w_new - w_old))
            #
            # # todo include termination criterion (weight change)
            if w_diff < w_diff_term_crit:
                # print "reg_param:",regularization ,"finished at iteration:", its, w_new
                # print "weights:", w_new
                # print "weight_difference:", w_diff
                break
            w_old = w_new

    loss_test = sess.run([loss], feed_dict={x_input: x_test, y_: y_test})
    loss_train = sess.run([loss], feed_dict={x_input: x, y_: y})
    res_dict = {"regularization": regularization, "iterations": its, "loss_test": loss_test, "loss_train": loss_train, "model:": (w__,b__)}
    sess.close()
    tf.reset_default_graph()
    return res_dict

def train_single_output_backup(x, y, x_test, y_test, learning_rate=0.0000005, max_iterations=1000000, regularization=1., w_diff_term_crit=0.0001, verbose=False, model=None):
    assert(x.shape[1] == x_test.shape[1],
           "train shape:" + str(x.shape) +
           " and test shape:" + str(x_test.shape) +
           " do not match in dimensionality")

    assert(x.shape[0] == y.shape[0],
           "number of training samples:" + str(x.shape) +
           " and number of labels:" + str(y.shape) +
           " do not match!")
    assert(x_test.shape[0] == y_test.shape[0],
           "number of testing samples:" + str(x_test.shape) +
           " and number of labels:" + str(y_test.shape) +
           " do not match!")

    # set up constants
    num_input_dims = x.shape[1]
    num_label_dims = y.shape[1]

    reg_fact = tf.constant(regularization, name='regularization_factor')

    with tf.name_scope('input'):
        x_input = tf.placeholder(tf.float32, shape=[None, num_input_dims], name='input')
    with tf.name_scope('target'):
        y_ = tf.placeholder(tf.float32, shape=[None, num_label_dims], name='target')

    # linear regression
    with tf.name_scope('linear_regression'):
        # init_vals = , name='truncated_normal_init_val_w')
        w = tf.Variable(tf.truncated_normal([num_input_dims, num_label_dims], stddev=1. / math.sqrt(2)), name='w')
        b = tf.Variable(tf.zeros([num_label_dims]), name='b')
        output = tf.matmul(x_input, w) + b

    with tf.name_scope('regularization'):
        # regularization_penalty = tf.reduce_sum(w, name='regularization_penalty_sum')
        # regularization_penalty *= reg_fact
        regularization_penalty = (tf.reduce_sum(tf.square(w)) * reg_fact)

    with tf.name_scope('loss'):
        # squared error loss + regularizationPenalty
        diff = y_ - output
        sq_diff = tf.square(diff)
        loss = tf.reduce_mean(sq_diff) + regularization_penalty
        # loss = tf.reduce_mean(sq_diff)

    with tf.name_scope('optimizer'):
        opt = tf.train.GradientDescentOptimizer(learning_rate)
        grads = opt.compute_gradients(loss)
        opt = opt.apply_gradients(grads)


    init = tf.initialize_all_variables()
    sess = tf.Session()

    sess.run(init)

    its = 0
    loss_train = -1.

    w_old = sess.run(w)[0][0]
    for i in xrange(0,max_iterations):
        w__, b__, output__, diff__, sq_diff__, loss__, _, regularization_penalty__ = sess.run([w, b, output, diff, sq_diff, loss, opt, regularization_penalty], feed_dict={x_input: x, y_: y})
        # if i % 1 and verbose:
        print "iteration:", i
        print "w__", w__
        print "b__", b__
        # print "diff__", diff__
        # print "sq_diff__", sq_diff__
        print "loss__", loss__
        print "regularization_penalty__", regularization_penalty__
        # print "regularization_penalty:", regularization_penalty__
        # print "iteration:", i
        # print "weight:", w__
        # print "loss:", loss__
        print ""
        w_new = sess.run(w)[0][0]
        its += 1
        w_diff = np.sum(np.abs(w_new - w_old))

        # todo include termination criterion (weight change)
        if w_diff < w_diff_term_crit:
            # print "reg_param:",regularization ,"finished at iteration:", its, w_new
            # print "weights:", w_new
            # print "weight_difference:", w_diff
            break
        w_old = w_new

    loss_test = sess.run([loss], feed_dict={x_input: x_test, y_: y_test})
    loss_train = sess.run([loss], feed_dict={x_input: x, y_: y})
    res_dict = {"regularization": regularization, "iterations": its, "loss_test": loss_test, "loss_train": loss_train, "model:": (w__,b__)}
    sess.close()
    tf.reset_default_graph()
    return res_dict
