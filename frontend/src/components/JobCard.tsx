import { useState } from 'react';
import { createPortal } from 'react-dom';
import {
  Bookmark,
  BookmarkX,
  CheckCircle,
  MapPin,
  DollarSign,
  Briefcase,
  ExternalLink,
} from 'lucide-react';
import { toast } from 'sonner';
import { Job } from '../App';
import JobDetailModal from './JobDetailModal';

interface JobCardProps {
  job: Job;
  onSave: (job: Job) => void;
  onUnsave: (job: Job) => void;
  onApply: (job: Job) => void;
  onChoose: (job: Job) => void;
  isSaved: boolean;
  isApplied: boolean;
}

interface ApplyConfirmationModalProps {
  isOpen: boolean;
  job: Job;
  onConfirm: () => void;
  onCancel: () => void;
}

function ApplyConfirmationModal({
  isOpen,
  job,
  onConfirm,
  onCancel,
}: ApplyConfirmationModalProps) {
  if (!isOpen) return null;

  const modalRoot = document.getElementById('modal-root') || document.body;

  return createPortal(
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
      }}>
      <div className='bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl'>
        <h3 className='text-lg font-semibold text-gray-900 mb-2'>
          Confirm Application
        </h3>
        <p className='text-gray-600 mb-4'>
          Did you complete your application for{' '}
          <span className='font-medium'>{job.title}</span> at{' '}
          <span className='font-medium'>{job.company}</span>?
        </p>
        <div className='flex gap-3'>
          <button
            onClick={onCancel}
            className='flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors'>
            No, I didn't apply
          </button>
          <button
            onClick={onConfirm}
            className='flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors'>
            Yes, I applied!
          </button>
        </div>
      </div>
    </div>,
    modalRoot
  );
}

export default function JobCard({
  job,
  onSave,
  onUnsave,
  onApply,
  onChoose,
  isSaved,
  isApplied,
}: JobCardProps) {
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showApplyConfirmation, setShowApplyConfirmation] = useState(false);

  const handleSaveToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isSaved) {
      onUnsave(job);
      toast.success('Job removed from saved!');
    } else {
      onSave(job);
      toast.success('Job saved successfully!');
    }
  };

  const handleApply = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isApplied) {
      toast.info('You already applied to this job');
      return;
    }

    // Open the job link in a new tab
    if (job.applyLink) {
      window.open(job.applyLink, '_blank');
    }

    // Show confirmation modal
    setShowApplyConfirmation(true);
  };

  const handleConfirmApply = () => {
    onApply(job);
    setShowApplyConfirmation(false);
    toast.success('Application recorded!', {
      description: `You've applied to ${job.title} at ${job.company}`,
    });
  };

  const handleCancelApply = () => {
    setShowApplyConfirmation(false);
  };

  const handleChoose = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChoose(job);
  };

  const handleCardClick = () => {
    setShowDetailModal(true);
  };

  return (
    <>
      <div
        className='bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow cursor-pointer'
        onClick={handleCardClick}>
        {/* Header */}
        <div className='flex items-start justify-between mb-4'>
          <div className='flex-1'>
            <div className='flex items-center gap-2 mb-2'>
              <h3 className='text-gray-900 font-medium'>{job.title}</h3>
              {isApplied && (
                <span className='px-2 py-1 bg-green-100 text-green-700 text-xs rounded'>
                  Applied
                </span>
              )}
              {isSaved && !isApplied && (
                <span className='px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded'>
                  Saved
                </span>
              )}
            </div>
            <p className='text-gray-700'>{job.company}</p>
          </div>
          <button
            onClick={handleSaveToggle}
            className={`p-2 rounded-lg transition-colors ${
              isSaved
                ? 'bg-blue-100 text-blue-600'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            title={isSaved ? 'Unsave job' : 'Save job'}>
            {isSaved ? (
              <BookmarkX className='w-5 h-5' />
            ) : (
              <Bookmark className='w-5 h-5' />
            )}
          </button>
        </div>

        {/* Job Details */}
        <div className='space-y-2 mb-4'>
          <div className='flex items-center gap-2 text-gray-600'>
            <Briefcase className='w-4 h-4' />
            <span className='text-sm'>{job.role}</span>
          </div>
          <div className='flex items-center gap-2 text-gray-600'>
            <MapPin className='w-4 h-4' />
            <span className='text-sm'>{job.location}</span>
            {job.isRemote && (
              <span className='px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded'>
                Remote
              </span>
            )}
          </div>
          <div className='flex items-center gap-2 text-gray-600'>
            <DollarSign className='w-4 h-4' />
            <span className='text-sm'>{job.salary}</span>
          </div>
        </div>

        {/* Description */}
        <p className='text-gray-600 text-sm mb-6 line-clamp-3'>
          {job.description}
        </p>

        {/* Actions */}
        <div className='flex gap-3'>
          <button
            onClick={handleChoose}
            className='flex-1 px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors'>
            Choose
          </button>
          <button
            onClick={handleApply}
            disabled={isApplied}
            className={`flex-1 px-4 py-2 rounded-lg transition-colors flex items-center justify-center gap-2 ${
              isApplied
                ? 'bg-green-100 text-green-700 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}>
            {isApplied ? (
              <>
                <CheckCircle className='w-4 h-4' />
                Applied
              </>
            ) : (
              <>
                <ExternalLink className='w-4 h-4' />
                Apply
              </>
            )}
          </button>
        </div>
      </div>

      {/* Job Detail Modal */}
      <JobDetailModal
        job={job}
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        onSave={onSave}
        onUnsave={onUnsave}
        onApply={(j) => {
          onApply(j);
          toast.success('Application recorded!', {
            description: `You've applied to ${j.title} at ${j.company}`,
          });
        }}
        isSaved={isSaved}
        isApplied={isApplied}
      />

      {/* Apply Confirmation Modal */}
      <ApplyConfirmationModal
        isOpen={showApplyConfirmation}
        job={job}
        onConfirm={handleConfirmApply}
        onCancel={handleCancelApply}
      />
    </>
  );
}
