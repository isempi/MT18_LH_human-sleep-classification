import itertools
import os
import shutil
import sys
import glob
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
#
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from matplotlib import gridspec

CLASSES = ['W', 'N1', 'N2', 'N3', 'REM']


def get_basename_(path):
    return os.path.basename(os.path.normpath(path))

def cm_figure_(prediction, truth, classes):
    classes = classes.copy()
    cm = confusion_matrix(truth, prediction, labels=range(len(classes)))
    num_classes = cm.shape[0]
    per_class_metrics = np.array(
        precision_recall_fscore_support(truth, prediction, beta=1.0,
                                        labels=range(
                                            len(classes)))).T.round(2)
    cm_norm = cm.astype('float') * 1 / (cm.sum(axis=1)[:, np.newaxis]+1e-7)
    cm_norm = np.nan_to_num(cm_norm, copy=True)

    fig = plt.figure(figsize=(3, 2), dpi=320, facecolor='w',
                     edgecolor='k')
    ax = fig.add_subplot(1, 1, 1)
    im = ax.imshow(
        np.concatenate((cm, np.zeros((len(classes), 4))), axis=1),
        cmap='Oranges')
    classes += ['PR', 'RE', 'F1', 'S']
    xtick_marks = np.arange(len(classes))
    ytick_marks = np.arange(len(classes) - 4)

    ax.set_xlabel('Predicted', fontsize=6, weight='bold')
    ax.set_xticks(xtick_marks)
    c = ax.set_xticklabels(classes, fontsize=4, ha='center')
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    ax.set_ylabel('True Label', fontsize=6, weight='bold')
    ax.set_yticks(ytick_marks)
    ax.set_yticklabels(classes[:-4], fontsize=4, va='center')
    ax.yaxis.set_label_position('left')
    ax.yaxis.tick_left()

    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        ax.text(j, i, '{}\n({:.2f})'.format(cm[i, j], cm_norm[i, j]),
                horizontalalignment="center", fontsize=2,
                verticalalignment='center', color="black")
    for i, j in itertools.product(range(cm.shape[0]),
                                  range(cm.shape[1], cm.shape[1] + 4)):
        val = per_class_metrics[i, j - num_classes]
        ax.text(j, i, val if j != cm.shape[1] + 3 else int(val),
                horizontalalignment="center", fontsize=2,
                verticalalignment='center', color="black")

    plt.subplots_adjust(bottom=0.1, right=0.8, top=0.7)
    return fig

def table_plot_(table, subjects, models):
    num_subjects = len(subjects)
    model_names = [get_basename_(f) for f in models]

    aggs = np.stack([np.mean(table, 0), np.std(table, 0)], axis=0)

    fig = plt.figure(figsize=(8.27, 11.69), dpi=320, facecolor='w',
                     edgecolor='k')
    gs = gridspec.GridSpec(num_subjects + 4, len(model_names))
    ax1 = fig.add_subplot(gs[:num_subjects, :])
    # plt.suptitle(PREFIX, fontsize=12)
    # ax1 =  plt.subplot(211)#fig.add_subplot(2, 1, 1)
    ax1.imshow(table[:num_subjects], cmap='Oranges', aspect="auto")

    for i, j in itertools.product(range(num_subjects),
                                  range(table.shape[1])):
        ax1.text(j, i, '{:.1f}'.format(table[i, j]),
                 horizontalalignment="center", fontsize=8,
                 verticalalignment='center', color="black")
    ytick_marks = np.arange(num_subjects)
    ax1.set_yticks(ytick_marks)
    ax1.set_yticklabels(subjects)
    ax1.set_xticklabels([])

    ax2 = fig.add_subplot(gs[num_subjects + 1:, :])
    ax2.imshow(aggs, cmap='Oranges', aspect="auto")
    # ax2.set_aspect('equal', 'box')
    # plt.imshow(table,cmap='Oranges')
    for i, j in itertools.product(range(aggs.shape[0]),
                                  range(aggs.shape[1])):
        ax2.text(j, i, '{:.2f}'.format(aggs[i, j]),
                 horizontalalignment="center", fontsize=8,
                 verticalalignment='center', color="black")
    xtick_marks = np.arange(len(model_names))
    ax2.set_xticks(xtick_marks)
    ax2.set_xticklabels(model_names, rotation=45)

    ytick_marks = np.arange(2)
    ax2.set_yticks(ytick_marks)
    ax2.set_yticklabels(['mean', 'std'])
    return fig


class Evaluation(object):
    def __init__(self, path):
        self.models = sorted(glob.glob(path + '/*'))
        self.path = path

    def cm(self):
        subjects = sorted(glob.glob(self.models[0] + '/*'))
        subjects = [get_basename_(f) for f in subjects]

        for i, model in enumerate(self.models):
            truth = []
            prediction = []
            for subject in subjects:
                path = os.path.join(model, subject)
                result = self.read_subject_file(path)
                truth.append(result['y_true'])
                prediction.append(result['y_pred'])
            truth = list(itertools.chain.from_iterable(truth))
            prediction = list(itertools.chain.from_iterable(prediction))
            fig = cm_figure_(prediction, truth, CLASSES)
            fig.suptitle(get_basename_(model))

    def hypnogram(self, index=0):
        subjects = sorted(glob.glob(self.models[0] + '/*'))
        subject = [get_basename_(f) for f in subjects][index]

        f, axarr = plt.subplots(len(self.models), 1, squeeze=False,
                                sharex=True, sharey=True,
                                figsize=(15, 2.5*len(self.models)))
        f.suptitle(subject)
        #plt.suptitle("Hypnograms", fontsize=12)
        plt.yticks(range(5), ['W', 'N1', 'N2', 'N3', 'REM'])
        for i, model in enumerate(self.models):
            path = os.path.join(model, subject)
            result = self.read_subject_file(path)
            axarr[i,0].plot(range(len(result['y_pred'])), result['y_pred'])
            axarr[i, 0].plot(range(len(result['y_true'])), result[
                'y_true'], alpha=0.3)

            wrong = np.argwhere(np.not_equal(result['y_true'], result[
                'y_pred']))
            axarr[i,0].plot(wrong, result['y_pred'][wrong], 'r.')
            acc = result['acc']
            axarr[i,0].set_title(f"{get_basename_(model)} "
                                 f"[{acc:.2f}%]")

            if 'attention' in result.keys():
                ax2 = axarr[i,0].twinx()
                # same x-axis
                color = 'tab:green'
                ax2.set_ylabel('attention', color=color)
                attention = result['attention']
                ax2.plot(range(len(attention)), attention, color=color)
                ax2.tick_params(axis='y', labelcolor=color)
                ax2.set_ylim(0, 1)

    def table(self):
        subjects = sorted(glob.glob(self.models[0] + '/*'))
        subjects = [get_basename_(f) for f in subjects]

        table = []
        for subject in subjects:
            row = []
            for i, model in enumerate(self.models):
                path = os.path.join(model, subject)
                result = self.read_subject_file(path)
                row.append(result['acc'])
            table.append(row)
        table = np.stack(table)
        table_plot_(table, subjects, self.models)

    def att_table(self):
        subjects = sorted(glob.glob(self.models[0] + '/*'))
        subjects = [get_basename_(f) for f in subjects]
        attention_models = []
        table = []
        first = True
        for subject in subjects:
            row = []
            for i, model in enumerate(self.models):
                path = os.path.join(model, subject)
                result = self.read_subject_file(path)
                if not 'attention' in result.keys():
                    continue
                row.append(np.mean(result['attention']))
                if first:
                    attention_models.append(get_basename_(model))
            table.append(row)
            first = False
        table = np.stack(table)
        table_plot_(table, subjects, attention_models)

    def extract_experts(self):
        model = self.models[0]
        subjects = sorted(glob.glob(self.models[0] + '/*'))
        subjects = [get_basename_(f) for f in subjects]
        experts = None
        for subject in subjects:
            path = os.path.join(model, subject)
            result = self.read_subject_file(path)
            if experts is None:
                experts = result['expert_channels']
                for expert in experts:
                    os.makedirs(os.path.join(self.path, 'Expert-'+expert))
            for i, expert in enumerate(experts):
                y_expert_prob = result['y_experts'][:, i, :]
                y_expert_pred = np.argmax(y_expert_prob, 1)
                y_true = result['y_true']
                a = result['a'][:, i]
                wrong = np.argwhere(np.not_equal(y_true, y_expert_pred))
                acc = 100*(1-wrong.shape[0]/len(y_expert_pred))
                savepath = os.path.join(self.path, 'Expert-'+expert, subject)
                savedict = {'y_true': y_true, 'y_pred': y_expert_pred,
                            'acc': acc, 'attention': a}
                np.savez(savepath, **savedict)

    def extract_voters(self):

        def get_acc(prediction, truth):
            wrong = np.argwhere(np.not_equal(truth, prediction))
            acc = 100 * (1 - (len(wrong) / len(truth)))
            return acc

        voting_models = ['SOFT-V', 'MAJ-V', 'U-BOUND']

        for new_model in voting_models:
            path = os.path.join(self.path, new_model)
            if os.path.exists(path) and os.path.isdir(path):
                shutil.rmtree(path)
        self.models = sorted(glob.glob(self.path + '/*'))

        for new_model in voting_models:
            os.makedirs(os.path.join(self.path, new_model))

        subjects = sorted(glob.glob(self.models[0] + '/*'))
        subjects = [get_basename_(f) for f in subjects]

        for subject in subjects:
            hard_votes = []
            soft_votes = []
            for i, model in enumerate(self.models):
                path = os.path.join(model, subject)
                result = self.read_subject_file(path)
                hard_votes.append(result['y_pred'])
                soft_votes.append(result['probs'])

            soft_votes = np.array(soft_votes)
            soft_vote = np.mean(soft_votes, axis=0)
            soft_vote = np.argmax(soft_vote, axis=1)
            savepath = os.path.join(self.path, 'SOFT-V', subject)
            savedict = {'y_true': result['y_true'], 'y_pred': soft_vote,
                        'acc': get_acc(soft_vote, result['y_true'])}
            np.savez(savepath, **savedict)


            hard_votes = np.array(hard_votes)
            from scipy.stats import mode
            maj_vote = mode(hard_votes, axis=0)[0][0]
            savepath = os.path.join(self.path, 'MAJ-V', subject)
            savedict = {'y_true': result['y_true'], 'y_pred': maj_vote,
                        'acc': get_acc(maj_vote, result['y_true'])}
            np.savez(savepath, **savedict)

            correct = np.equal(hard_votes, result['y_true'])
            ubound = np.any(correct, axis=0)
            ubound_vote = maj_vote
            ubound_vote[ubound] = result['y_true'][ubound]

            savepath = os.path.join(self.path, 'U-BOUND', subject)
            savedict = {'y_true': result['y_true'], 'y_pred': ubound_vote,
                        'acc': get_acc(ubound_vote, result['y_true'])}
            np.savez(savepath, **savedict)


    def read_subject_file(self, path):
        file = np.load(path)
        truth = file['truth'] if 'truth' in file.keys() else file[
            'y_true']
        pred = file['pred'] if 'pred' in file.keys() else file['y_pred']
        acc = float(file['acc'])

        result = {'y_true': truth, 'y_pred': pred, 'acc': acc}
        if 'probs' in file.keys():
            result['probs'] = file['probs']
        if 'y_probs' in file.keys():
            result['probs'] = file['y_probs']
        if 'expert_channels' in file.keys():
            result['expert_channels'] = file['expert_channels']
        if 'y_experts'  in file.keys():
            result['y_experts'] = file['y_experts']
        if 'a' in file.keys():
            result['a'] = file['a']
        if 'attention' in file.keys():
            result['attention'] = file['attention']
        return result


if __name__ == '__main__':
    e = Evaluation(sys.argv[1])
    #e.table()
    #e.extract_voters()
    e.att_table()