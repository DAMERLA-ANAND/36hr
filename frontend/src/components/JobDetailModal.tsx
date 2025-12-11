import { useState } from 'react';
import { createPortal } from 'react-dom';
import {
  X,
  Bookmark,
  BookmarkX,
  ExternalLink,
  MapPin,
  DollarSign,
  Briefcase,
  Clock,
  Building2,
  CheckCircle,
} from 'lucide-react';
import { Job } from '../App';

interface JobDetailModalProps {
  job: Job;
  isOpen: boolean;
  onClose: () => void;
  onSave: (job: Job) => void;
  onUnsave: (job: Job) => void;
  onApply: (job: Job) => void;
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

export default function JobDetailModal({
  job,
  isOpen,
  onClose,
  onSave,
  onUnsave,
  onApply,
  isSaved,
  isApplied,
}: JobDetailModalProps) {
  const [showApplyConfirmation, setShowApplyConfirmation] = useState(false);

  if (!isOpen) return null;

  const handleApplyClick = () => {
    if (isApplied) return;

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
  };

  const handleCancelApply = () => {
    setShowApplyConfirmation(false);
  };

  const handleSaveToggle = () => {
    if (isSaved) {
      onUnsave(job);
    } else {
      onSave(job);
    }
  };

  const modalRoot = document.getElementById('modal-root') || document.body;

  const modalContent = (
    <>
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
          zIndex: 9999,
        }}
        onClick={onClose}>
        <div
          className='bg-white rounded-xl w-[90vw] h-[90vh] max-w-5xl overflow-hidden shadow-2xl flex flex-col'
          onClick={(e) => e.stopPropagation()}>
          {/* Header */}
          <div className='flex items-start justify-between p-6 border-b border-gray-200'>
            <div className='flex gap-4'>
              {job.employerLogo && (
                <img
                  src={job.employerLogo}
                  alt={job.company}
                  className='w-16 h-16 rounded-lg object-contain bg-gray-100 p-2'
                />
              )}
              <div>
                <div className='flex items-center gap-2 mb-1'>
                  <h2 className='text-2xl font-bold text-gray-900'>
                    {job.title}
                  </h2>
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
                <p className='text-lg text-gray-700 flex items-center gap-2'>
                  <Building2 className='w-5 h-5' />
                  {job.company}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className='p-2 hover:bg-gray-100 rounded-lg transition-colors'>
              <X className='w-6 h-6 text-gray-500' />
            </button>
          </div>

          {/* Content */}
          <div className='flex-1 overflow-y-auto p-6'>
            {/* Job Meta */}
            <div className='grid grid-cols-2 md:grid-cols-4 gap-4 mb-6'>
              <div className='flex items-center gap-2 text-gray-600'>
                <MapPin className='w-5 h-5' />
                <span>{job.location}</span>
                {job.isRemote && (
                  <span className='px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded'>
                    Remote
                  </span>
                )}
              </div>
              <div className='flex items-center gap-2 text-gray-600'>
                <Briefcase className='w-5 h-5' />
                <span>{job.role}</span>
              </div>
              <div className='flex items-center gap-2 text-gray-600'>
                <DollarSign className='w-5 h-5' />
                <span>{job.salary}</span>
              </div>
              {job.postedAt && (
                <div className='flex items-center gap-2 text-gray-600'>
                  <Clock className='w-5 h-5' />
                  <span>Posted: {job.postedAt}</span>
                </div>
              )}
            </div>

            {/* Description */}
            <div className='mb-6'>
              <h3 className='text-lg font-semibold text-gray-900 mb-3'>
                Job Description
              </h3>
              <div className='text-gray-700 whitespace-pre-wrap'>
                {job.description}
              </div>
            </div>

            {/* Highlights */}
            {job.highlights && (
              <div className='space-y-4'>
                {job.highlights.Qualifications &&
                  job.highlights.Qualifications.length > 0 && (
                    <div>
                      <h3 className='text-lg font-semibold text-gray-900 mb-3'>
                        Qualifications
                      </h3>
                      <ul className='list-disc list-inside space-y-1 text-gray-700'>
                        {job.highlights.Qualifications.map((qual, index) => (
                          <li key={index}>{qual}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                {job.highlights.Responsibilities &&
                  job.highlights.Responsibilities.length > 0 && (
                    <div>
                      <h3 className='text-lg font-semibold text-gray-900 mb-3'>
                        Responsibilities
                      </h3>
                      <ul className='list-disc list-inside space-y-1 text-gray-700'>
                        {job.highlights.Responsibilities.map((resp, index) => (
                          <li key={index}>{resp}</li>
                        ))}
                      </ul>
                    </div>
                  )}
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className='p-6 border-t border-gray-200 flex gap-4'>
            <button
              onClick={handleSaveToggle}
              className={`flex-1 px-6 py-3 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                isSaved
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}>
              {isSaved ? (
                <>
                  <BookmarkX className='w-5 h-5' />
                  Unsave Job
                </>
              ) : (
                <>
                  <Bookmark className='w-5 h-5' />
                  Save Job
                </>
              )}
            </button>
            <button
              onClick={handleApplyClick}
              disabled={isApplied}
              className={`flex-1 px-6 py-3 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                isApplied
                  ? 'bg-green-100 text-green-700 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}>
              {isApplied ? (
                <>
                  <CheckCircle className='w-5 h-5' />
                  Already Applied
                </>
              ) : (
                <>
                  <ExternalLink className='w-5 h-5' />
                  Apply Now
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Apply Confirmation Modal */}
      <ApplyConfirmationModal
        isOpen={showApplyConfirmation}
        job={job}
        onConfirm={handleConfirmApply}
        onCancel={handleCancelApply}
      />
    </>
  );

  return createPortal(modalContent, modalRoot);
}
